import { useEffect, useState } from "react";
import { Button, Col, Container, Row } from "react-bootstrap";

function Answer(props: { text: string, handleAnswer: Function }) {
    return <Row className="center-items">
        <Button variant="outline-dark" className="question-answer mt-1" onClick={() => props.handleAnswer(props.text)} >
            {props.text}
        </Button>
    </Row>
}

function Question(props: { id: number, setId: Function }) {
    
    const [message, setMessage] = useState<string>("");
    const [questionData, setQuestionData] = useState<any>({})
    
    function handleCorrect() {
        props.setId(props.id + 1);
        setMessage("");
    };
    function handleWrong() {
        props.setId(1);
        setMessage("");
    };
    function handleAnswer(ans: string) {
        fetch(`/api/answer`, {
            method: "POST",
            body: JSON.stringify({ answer: ans }),
            headers: {
                "Content-Type": "application/json",
            },
            credentials: 'include',
        })
            .then(response => response.json())
            .then(json => {
                if (json.error) {
                    console.error(json);
                }
                else {
                    setMessage(json.correct === true ? "Correct!" : "Wrong!");
                    if(json.message.length > 0){
                        setMessage(json.message);
                    }
                }
            })
            .catch(error => {
                console.error(error);
            });
    };


    useEffect(() => {
        fetch(`/api/question/${props.id}`, {
            credentials: 'include',
        })
            .then(response => response.json())
            .then(json => {
                if (!json.question) {
                    console.error(json);
                }
                else {
                    setQuestionData(json);
                }
            })
            .catch(error => {
                console.error(error);
            });
    }, [props.id])


    return questionData.question ? <Container fluid className="mt-3">
        <Row className="center-items">
            <img alt="" src={`/api/qimages/${questionData.id}`} className="question-image"></img>
        </Row>
        <Row className="center-items question-text">
            {questionData.question}
        </Row>
        <Row className="justify-content-md-center">
            <Col sm={4}>
                {questionData.answers.map((a: string, i: number) => <Answer text={a} key={`ans-${i}`} handleAnswer={handleAnswer} />)}
            </Col>
        </Row>
        <Row className="justify-content-md-center mt-3">
            {message}
        </Row>
        {message === "" ?
            <></> :
            <Row className="justify-content-md-center mt-3">
                <Col className="center-items">
                    <Button onClick={message === "Correct!" ? handleCorrect : handleWrong}> {message === "Correct!" ? "Next" : "Retry"} </Button>
                </Col>
            </Row>
        }
        { questionData.prize ? <Row className="justify-content-md-center mt-3">We know you, here's the prize: {questionData.prize}</Row> : <></>}
    </Container> :
        <>
            No question
        </>
};

export default Question;