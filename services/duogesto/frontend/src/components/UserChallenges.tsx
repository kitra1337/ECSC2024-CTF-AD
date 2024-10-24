import { useState } from "react";
import { Button, Col, Container, Form, Row } from "react-bootstrap";
import Question from "./Question";

function ChallengeRow(props: { challenge: any, setSelectedChall: Function }) {
    return <Row className="mt-3">
        <Col sm={3}>
            {props.challenge._id}
        </Col>
        <Col sm={6}>
            {props.challenge.question}
        </Col>
        <Col sm={3}>
            <Button onClick={() => props.setSelectedChall(props.challenge._id)}>Play</Button>
        </Col>
    </Row>
};

function ChallengeList(props: { challenges: any, setSelectedChall: Function }) {
    return props.challenges.map((c: object, i: number) => <ChallengeRow challenge={c} key={`challrow-${i}`} setSelectedChall={props.setSelectedChall} />);
};

function UserChallenges() {

    const [username, setUsername] = useState<string>("");
    const [challenges, setChallenges] = useState<object>([]);
    const [selectedChall, setSelectedChall] = useState<string>('-1');

    function handleSearch(e: any) {
        e.preventDefault();

        if (username) {
            fetch(`/api/challenges/${username}`, {
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    setChallenges(json.challenges);
                })
                .catch(error => console.error(error));
        }
    };

    return <Container fluid>
        <Form className="mt-3 center-items">
            <Col sm={3}>
                <Row>
                    <Form.Group className="mb-3">
                        <Form.Control placeholder="Username" onChange={e => setUsername(e.target.value)} />
                    </Form.Group>
                </Row>
                <Row>
                    <Col>
                        <Button variant="primary" onClick={handleSearch}>
                            Search
                        </Button>
                    </Col>
                </Row>
            </Col>
        </Form>

        <Row className="center-items">
            <Row>
                <Col sm={3}>
                    ID
                </Col>
                <Col sm={6}>
                    Question
                </Col>
                <Col sm={3}>
                    Play
                </Col>
            </Row>
            <ChallengeList challenges={challenges} setSelectedChall={setSelectedChall} />
        </Row>

        {selectedChall != '-1' ?
        <Question id={selectedChall} setId={() => {}}/> :
            <></>}
    </Container>
};

export default UserChallenges;