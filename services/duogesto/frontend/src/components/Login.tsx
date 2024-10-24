import { useState } from "react";
import { Button, Col, Container, Form, Row } from "react-bootstrap";
import { useNavigate } from "react-router-dom";


function Login(props: { loggedIn: boolean, setLoggedIn: Function }) {

    const navigate = useNavigate();

    if (props.loggedIn) {
        navigate('/');
    }

    const [username, setUsername] = useState<string>("");
    const [password, setPassword] = useState<string>("");

    function handleLogin(e: any) {
        e.preventDefault();

        if (username && password) {
            fetch(`/api/login`, {
                method: "POST",
                body: JSON.stringify({ name: username, password: password }),
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    if(json.error){
                        props.setLoggedIn(false)
                    }
                    else{
                        props.setLoggedIn(true)
                    }
                })
                .catch(error => {
                    console.error(error);
                    props.setLoggedIn(false);
                });
        }
    };

    function handleRegister(e: any) {
        e.preventDefault();

        if (username && password) {
            fetch(`/api/register`, {
                method: "POST",
                body: JSON.stringify({ name: username, password: password }),
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    if(json.error){
                        props.setLoggedIn(false)
                    }
                    else{
                        props.setLoggedIn(true)
                    }
                })
                .catch(error => {
                    console.error(error);
                    props.setLoggedIn(false);
                });
        }
    };

    return <Container fluid>
        <Container className="center-items">
            <img alt="" src="/logo.png" className="mt-3"></img>
        </Container>
        <Form className="mt-3 center-items">
            <Col sm={3}>
                <Row>
                    <Form.Group className="mb-3">
                        <Form.Control placeholder="Username" onChange={e => setUsername(e.target.value)} />
                    </Form.Group>
                    <Form.Group className="mb-3">
                        <Form.Control placeholder="Password" onChange={e => setPassword(e.target.value)} />
                    </Form.Group>
                </Row>
                <Row>
                    <Col>
                        <Button variant="primary" onClick={handleLogin}>
                            Login
                        </Button>
                    </Col>
                    <Col>
                        <Button variant="primary" onClick={handleRegister}>
                            Register
                        </Button>
                    </Col>
                </Row>
            </Col>
        </Form>
    </Container>
};

export default Login;