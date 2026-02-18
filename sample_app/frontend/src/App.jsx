import { useState, useEffect } from 'react'

function App() {
    const [users, setUsers] = useState([])

    useEffect(() => {
        fetch('http://localhost:3000/api/users')
            .then(res => res.json())
            .then(data => setUsers(data))
            .catch(err => console.error(err))
    }, [])

    return (
        <div>
            <h1>User List</h1>
            <ul>
                {users.map((user, i) => (
                    <li key={i}>{user.name} ({user.email})</li>
                ))}
            </ul>
        </div>
    )
}

export default App
