import { useState } from "react";
import Question from "./Question";
import { Col, Container } from "react-bootstrap";

function Quiz() {

    const [id, setId] = useState<number>(1);

    return <Container fluid>
        <Col className="center-items" >
            <h1> Question {id} </h1>
        </Col>
        <Question id={id} setId={setId} />
    </Container>
};

export default Quiz;