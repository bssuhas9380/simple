const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');

const app = express();
app.use(cors());
app.use(express.json());

let todos = [];

app.get('/api/todos', (req, res) => {
    res.json({ success: true, data: todos, count: todos.length });
});

app.post('/api/todos', (req, res) => {
    const { title, description } = req.body;
    if (!title) return res.status(400).json({ error: 'Title is required' });
    const todo = { id: uuidv4(), title, description: description || '', done: false, createdAt: new Date() };
    todos.push(todo);
    res.status(201).json({ success: true, data: todo });
});

app.put('/api/todos/:id', (req, res) => {
    const todo = todos.find(t => t.id === req.params.id);
    if (!todo) return res.status(404).json({ error: 'Not found' });
    Object.assign(todo, req.body);
    res.json({ success: true, data: todo });
});

app.delete('/api/todos/:id', (req, res) => {
    const idx = todos.findIndex(t => t.id === req.params.id);
    if (idx === -1) return res.status(404).json({ error: 'Not found' });
    todos.splice(idx, 1);
    res.json({ success: true, message: 'Deleted' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`TODO API running on port ${PORT}`));
