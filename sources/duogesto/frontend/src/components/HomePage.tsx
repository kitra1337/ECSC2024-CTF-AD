import { Button, Col, Container, Row } from "react-bootstrap";
import { Link } from "react-router-dom";

function HomePage(props: { loggedIn: boolean }) {
    return <Container fluid className="homepage">
        <img alt="" src="/logo.png" className="home-logo mt-3"></img>
        <h1> Duogesto </h1>
        <Row className="center-items mt-5 mb-5">
            <Col sm={8}>
                Discover the vibrant world of Italian communication beyond words! At Duogesto, we believe that understanding Italian gestures is key to truly connecting with the culture. Our platform offers a comprehensive guide to the rich tapestry of hand signs, facial expressions, and body language that shape everyday interactions in Italy.
            </Col>
        </Row>
        <Row className="mt-5 mb-5" >
            <Col>
                <Link to={props.loggedIn ? "/quiz" : "/login"} > <Button variant="success">Try it now!</Button> </Link>
            </Col>
        </Row>
        <Row className="mt-5 mb-5">
            <Col>
                <img alt="" src="/feat1.png" className="home-features"></img>
            </Col>
            <Col>
                <div className="home-features"> In our interactive lessons, you will explore the meanings behind iconic gestures, from the classic “Mamma Mia!” to the subtle nuances of conversation. Each gesture is presented with engaging visuals, contextual explanations, and cultural anecdotes that bring the meanings to life. Whether you're preparing for a trip to Italy, connecting with Italian-speaking friends, or simply curious about the culture, our application provides an immersive learning experience. </div>
            </Col>
        </Row>
        <Row className="mt-5 mb-5">
            <Col>
                <div className="home-features"> Join our community of learners and unlock the secrets of Italian non-verbal communication. With easy-to-follow tutorials, quizzes, and practical examples, you’ll gain confidence in your ability to express yourself like a local. Start your journey today and discover how gestures can transform your understanding of Italian culture and enhance your conversations! </div>
            </Col>
            <Col>
                <img alt="" src="/feat2.png" className="home-features"></img>
            </Col>
        </Row>
        <Row className="mt-5 mb-5" >
            <Col>
                <Link to={props.loggedIn ? "/quiz" : "/login"} > <Button variant="success">Try it now!</Button> </Link>
            </Col>
        </Row>
    </Container >
};

export default HomePage;