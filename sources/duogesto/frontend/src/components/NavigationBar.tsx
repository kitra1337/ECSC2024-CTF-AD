import { Container, Nav, Navbar } from "react-bootstrap";
import { Link } from "react-router-dom";

function NavigationBar(props: { loggedIn: boolean, setLoggedIn: Function, setUsername: Function }) {

    fetch(`/api/me`, {
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    if(json.error){
                        props.setLoggedIn(false);
                    }
                    else{
                        props.setLoggedIn(true);
                        props.setUsername(json.name);
                    }
                })
                .catch(_ => props.setLoggedIn(false));

    return <Navbar expand="lg" variant='dark' className="navigationbar">
        <Container fluid>
            <Navbar.Brand href="#">
                <img alt="" src="/logo.png" width="40" height="40" className="d-inline-block navbar-logo" />
                Duogesto
            </Navbar.Brand>
            <Nav className="me-auto">
                <Nav.Link as={Link} to={"/"}> Home </Nav.Link>
                {props.loggedIn ? <>
                    <Nav.Link as={Link} to={"/profile"}> Profile </Nav.Link>
                    <Nav.Link as={Link} to={"/quiz"}> Take quiz </Nav.Link>
                    <Nav.Link as={Link} to={"/createchall"}> Create challenge </Nav.Link>
                    <Nav.Link as={Link} to={"/userchall"}> User challenges </Nav.Link>
                    <Nav.Link as={Link} to={"/friends"}> Friends </Nav.Link>
                    <Nav.Link as={Link} to={"/logout"}> Logout </Nav.Link>
                </> :
                    <Nav.Link as={Link} to={"/login"}> Login </Nav.Link>}
            </Nav>
        </Container>
    </Navbar>
};

export default NavigationBar;