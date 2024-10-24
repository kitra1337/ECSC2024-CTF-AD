import { useState } from "react";
import { Alert, Button, Col, Form, Row } from "react-bootstrap";

function AnswerRow(props: { idx: number, answers: any, setAnswers: Function }) {
    return <Row>
        <Col sm={10}>
            <Form.Group className="mb-3">
                <Form.Label>
                    Answer {props.idx}
                </Form.Label>
                <Form.Control placeholder="" onChange={(e: any) => {
                    let anscopy: any = { ...props.answers };
                    anscopy[props.idx] = { answer: e.target.value, correct: props.answers[props.idx].correct };
                    props.setAnswers(anscopy);
                }} />
            </Form.Group>
        </Col>
        <Col sm={2}>
            <Form.Group className="mb-3">
                <Form.Label>
                    Correct?
                </Form.Label>
                <Form.Check onChange={(e: any) => {
                    let anscopy: any = { ...props.answers };
                    anscopy[props.idx] = { answer: props.answers[props.idx].answer, correct: e.target.checked };
                    props.setAnswers(anscopy);
                }} />
            </Form.Group>
        </Col>
    </Row>
};

function CreateChallenge() {

    const [url, setUrl] = useState<string>("");
    const [name, setName] = useState<string>("");
    const [text, setText] = useState<string>("");
    const [answers, setAnswers] = useState<object>({
        1: { answer: "", correct: false },
        2: { answer: "", correct: false },
        3: { answer: "", correct: false },
    });
    const [prize, setPrize] = useState<string>("");
    const [message, setMessage] = useState<string>("");

    function handleSubmit(e: any) {
        e.preventDefault();

        if (url && name) {
            fetch(`/api/upload`, {
                method: "POST",
                body: JSON.stringify({ url: url, filename: name }),
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    console.log(json);
                })
                .catch(error => console.error(error));
        }

        if (text) {
            fetch(`/api/createchallenge`, {
                method: "POST",
                body: JSON.stringify({ text: text, image: name, answers: answers, prize: prize }),
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    setUrl("");
                    setName("");
                    setText("");
                    setAnswers({
                        1: { answer: "", correct: false },
                        2: { answer: "", correct: false },
                        3: { answer: "", correct: false },
                    });
                    setPrize("");
                    let elements = document.getElementsByClassName("form-control");
                    for (let i: number = 0; i < elements.length; i++) {
                        let el: any = elements.item(i);
                        if (el) {
                            el.value = "";
                        }
                    }
                    setMessage("Challenge created");
                })
                .catch(error => console.error(error));
        }
    };

    return <>
        {
            message ?
            <Alert variant="success"> {message} </Alert> :
            <></>
        }
        <Form className="mt-3 center-items">
            <Col sm={5}>
                <Row>
                    <Form.Group className="mb-3">
                        <Form.Label>
                            Image URL
                        </Form.Label>
                        <Form.Control placeholder="" onChange={(e: any) => setUrl(e.target.value)} />
                    </Form.Group>
                    <Form.Group className="mb-3">
                        <Form.Label>
                            Image name
                        </Form.Label>
                        <Form.Control placeholder="" onChange={(e: any) => setName(e.target.value)} />
                    </Form.Group>
                    <Form.Group className="mb-3">
                        <Form.Label>
                            Question text
                        </Form.Label>
                        <Form.Control placeholder="" onChange={(e: any) => setText(e.target.value)} />
                    </Form.Group>
                    {[1, 2, 3].map((i: number) => <AnswerRow idx={i} key={`chalans-${i}`} answers={answers} setAnswers={setAnswers} />)}
                    <Form.Group className="mb-3">
                        <Form.Label>
                            Prize
                        </Form.Label>
                        <Form.Control placeholder="" onChange={(e: any) => setPrize(e.target.value)} />
                    </Form.Group>
                </Row>
                <Row>
                    <Col>
                        <Button variant="primary" onClick={handleSubmit}>
                            Submit
                        </Button>
                    </Col>
                </Row>
            </Col>
        </Form>
    </>
};

export default CreateChallenge;