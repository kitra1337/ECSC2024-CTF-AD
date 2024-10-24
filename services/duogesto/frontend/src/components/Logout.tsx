import { useNavigate } from "react-router-dom";

function Logout(props: {setLoggedIn: Function}) {
    
    const navigate = useNavigate();

    fetch(`/api/logout`, {
                credentials: 'include',
            })
                .then(response => response.json())
                .then(json => {
                    props.setLoggedIn(false);
                    navigate('/');
                })
                .catch(error => {
                    console.error(error);
                });

    return <>
        Logging out...
    </>
};

export default Logout;