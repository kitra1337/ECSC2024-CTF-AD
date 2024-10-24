import { useEffect, useState } from "react";
import { Button, Col, Form, Row } from "react-bootstrap";



function Friends() {

    const [friends, setFriends] = useState<string[]>([]);
    const [friend, setFriend] = useState<string>("");

    function handleSubmit(e: any) {
        e.preventDefault();

        if (friend) {
            fetch(`/api/friends`, {
                method: "POST",
                body: JSON.stringify({ name: friend }),
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
    };

    useEffect(() => {
        fetch(`/api/friends`, {
            credentials: 'include',
        })
            .then(response => response.json())
            .then(json => {
                setFriends(json['friends']);
            })
            .catch(error => console.error(error));
    }, []);

    return <>

        <h1>Friends</h1>
        <ul>
            {friends.map((friend, index) => <li key={index}>{friend}</li>)}
        </ul>

        <Form className="mt-3 center-items">
            <Col sm={5}>
                <Row>
                    <Form.Group className="mb-3">
                        <Form.Label>
                            Name
                        </Form.Label>
                        <Form.Control placeholder="" onChange={(e: any) => setFriend(e.target.value)} />
                    </Form.Group>
                </Row>
                <Row>
                    <Col>
                        <Button variant="primary" onClick={handleSubmit}>
                            Add friend
                        </Button>
                    </Col>
                </Row>
            </Col>
        </Form>
    </>
};

export default Friends;