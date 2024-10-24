import { useState } from "react";
import { Button, Col, Container, Form, Row } from "react-bootstrap";
import { LuFileEdit } from "react-icons/lu";

function Profile(props: { username: string }) {

    const [url, setUrl] = useState<string>('');

    function handleUpload(e: any) {
        e.preventDefault();

        if (url) {
            fetch(`/api/upload`, {
                method: "POST",
                body: JSON.stringify({ url: url, filename: 'propic.png' }),
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    window.location.reload();
                })
                .catch(error => console.error(error));
        }
    };

    return <Container fluid>
        <Row>
            <Col>
                <Row className="mt-3 center-items">
                    <img alt="" src={`/api/propic`} className="user-pic"></img>
                </Row>
                <Row>
                    <Form className="mt-3 center-items">
                        <Form.Group as={Row}>
                            <Form.Label column sm={4}>Image URL</Form.Label>
                            <Col sm={8}>
                                <Form.Control placeholder="URL" onChange={e => setUrl(e.target.value)} />
                            </Col>
                        </Form.Group>
                        <Button className="user-edit-button" style={{ maxWidth: '100px' }} onClick={handleUpload} >
                            <LuFileEdit />
                        </Button>
                    </Form>
                </Row>
                <Row className="mt-3 center-items">
                    {props.username}
                </Row>
            </Col>
        </Row>
    </Container>
};

export default Profile;