import express from 'express';
import { MongoClient } from 'mongodb';
import bodyParser from 'body-parser';
import session from 'express-session'
import MongoStore from 'connect-mongo'
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import 'express-async-errors';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(bodyParser.json());

const MONGO_URL = `mongodb://${process.env.MONGO_HOST}:27017`
const SECRET_KEY = process.env.SECRET_KEY

async function connectToDatabase() {
    const client = new MongoClient(MONGO_URL);
    await client.connect();
    return client.db('db');
}

console.log('Connecting to database');

const db = await connectToDatabase();
const users = db.collection('users');
const questions = db.collection('questions');

// clear data every 5 minutes
setInterval(async () => {

    console.log('Clearing old data...');

    try {
        // remove data older than 15 minutes
        await questions.deleteMany({ created: { $lt: new Date(Date.now() - 15*60*1000) } });
        await users.deleteMany({ created: { $lt: new Date(Date.now() - 15*60*1000) } });

        spawn('/usr/bin/find', [`${__dirname}/files/`, '-mindepth', '1', '-type', 'd', '-mmin', '+15', '-exec', '/usr/bin/rm', '-rf', '{}', ';'], { uid: 1000 });
        spawn('/usr/bin/find', [`${__dirname}/prizes/`, '-mindepth', '1', '-mmin', '+15', '-delete']);
    } catch (error) {
        console.error('Failed to clear old data', error);
    }

}, 5*60*1000);

app.use(session({
    secret: SECRET_KEY,
    store: MongoStore.create({ mongoUrl: MONGO_URL }),
}));

app.options("/*", function (req, res, next) {
    res.sendStatus(200);
});

app.post("/register", async function (req, res) {
    const user = req.body;

    if (!user.name || !user.password) {
        return res.status(400).json({ error: "Invalid user" });
    }
    
    if(user.name.trim() === "" || user.name.includes('/')) {
        return res.status(400).json({ error: "Invalid username" });
    }

    // check if user already exists
    const existingUser = await users.findOne({ name: user.name });
    if (existingUser) {
        return res.status(400).json({ error: "User already exists" });
    }

    let newUser = {
        name: user.name,
        password: user.password,
        friends: [],
        created: new Date()
    };

    await users.insertOne(newUser);

    fs.mkdirSync(__dirname + '/files/' + user.name);
    fs.chownSync(__dirname + '/files/' + user.name, 1000, 1000);

    req.session.user = user;
    return res.json({ message: "User created" });
});


app.post("/login", async function (req, res) {
    const user = req.body;

    if (!user.name || !user.password) {
        return res.status(400).json({ error: "Invalid user" });
    }

    if(user.name.trim() === "" || user.name.includes('/')) {
        return res.status(400).json({ error: "Invalid username" });
    }

    const existingUser = await users.findOne({ name: user.name });
    if (!existingUser) {
        return res.status(400).json({ error: "User not found" });
    }

    if (user.password !== existingUser.password) {
        return res.status(400).json({ error: "Invalid password" });
    }

    req.session.user = existingUser;
    return res.json({ message: "Logged in" });
});


app.get("/logout", function (req, res) {
    req.session.destroy();
    return res.json({ message: "Logged out" });
});


app.use(function (req, res, next) {
    if (!req.session.user) {
        return res.status(401).json({ error: "Not logged in" });
    }
    next();
});


app.get("/me", function (req, res) {
    return res.json({name: req.session.user?.name});
});

app.get("/propic", function (req, res) {
    let username = req.session.user?.name;

    if (!fs.existsSync(`${__dirname}/files/${username}/propic.png`)) {
        return res.sendFile(`/default.png`, { root: __dirname });
    }

    res.sendFile(`/files/${username}/propic.png`, { root: __dirname });
});

app.post("/friends", async function (req, res) {
    const newfriend = req.body.name;
    const me = req.session.user?.name;

    if (!newfriend || newfriend.trim() === "") {
        return res.status(400).json({ error: "Invalid friend" });
    }

    const existingUser = await users.findOne({ name: newfriend });
    if (!existingUser) {
        return res.status(400).json({ error: "Friend not found" });
    }

    await users.updateOne({ name: existingUser.name }, { $addToSet: { friends: me } });
    return res.json({ message: "Friend added" });
});

app.get("/friends", async function (req, res) {
    const me = req.session.user?.name;
    const existingUser = await users.findOne({ name: me });

    return res.json({ friends: existingUser.friends || [] });
});

app.post("/upload", function (req, res) {
    let username = req.session.user?.name;

    const url = req.body.url;
    const filename = path.basename(req.body.filename);

    try{
        let x = spawn('/usr/bin/curl', ['--max-filesize', '1M', url, '-o', filename], { cwd: `${__dirname}/files/${username}`, uid: 1000, timeout:3000});
        
        x.on('close', (code) => {
            if (code !== 0) {
                console.log(`child process exited with code ${code}`);
                return res.status(500).json({ error: "Failed to download image" });
            }
            return res.json({ success: true });
        });
    } catch (e) {
        return res.status(500).json({ error: "Failed to download image" });
    }
});

app.get("/question/:qid", async function (req, res) {
    let qid = +req.params.qid;

    const existingQuestion = await questions.findOne({ id: qid });

    if (!existingQuestion) {
        return res.status(400).json({ error: "Question not found" });
    }

    req.session.author = existingQuestion.author;
    req.session.correct = existingQuestion.correct;
    req.session.endquiz = existingQuestion.id === 5;

    delete existingQuestion.correct
    
    if (existingQuestion.author) {
        if (existingQuestion.author === req.session.user?.name || req.session.user?.friends?.includes(existingQuestion.author)) {
            existingQuestion.prize = fs.readFileSync(`${__dirname}/prizes/${existingQuestion.author}`).toString();  
        } 
    }
   
    res.json(existingQuestion);
});

app.post("/answer", async function (req, res) {
    let answer = req.body.answer;
    let message = "";


    if (!req.session.correct) {
        return res.status(400).json({ error: "No active question!" });
    }

    let correct =  req.session.correct.indexOf(answer) !== -1;

    if (req.session.endquiz && correct) {
        message = "Congratulations! You completed the quiz!";
    }

    if (req.session.author !== "" && correct) {
        message = fs.readFileSync(`${__dirname}/prizes/${req.session.author}`).toString();
    }

    res.json({ correct: correct, message: message });
});

app.get("/qimages/:qid", async function (req, res) {
    let qid = +req.params.qid;

    if (qid) {
        const imagename = (await questions.findOne({ id: qid })).image;

        if (!fs.existsSync(`${__dirname}/${imagename}`)) {
            return res.json({ error: "Question image not found" });
        }
        else {
            return res.sendFile(`/${imagename}`, { root: __dirname });
        }
    }
    else {
        return res.json({ error: "Question id invalid" });
    }
});

app.post("/createchallenge", async function (req, res) {
    let challengeBody = req.body;

    let challenge = {
        image: `files/${req.session.user?.name}/${ path.basename(challengeBody.image) }`,
        question: challengeBody.text,
        answers: [1, 2, 3].map(i => challengeBody.answers[i].answer),
        correct: [1, 2, 3].filter(i => challengeBody.answers[i].correct).map(i => challengeBody.answers[i].answer),
        author: req.session.user?.name,
        created: new Date(),
    };

    if(!fs.existsSync(`${__dirname}/prizes/${req.session.user?.name}`)) {
        fs.writeFileSync(`${__dirname}/prizes/${req.session.user?.name}`, challengeBody.prize);
    }

    let cursor = questions.find().sort({ id: -1 }).limit(1);
    let id;
    for await (let doc of cursor){
        id = +doc.id;
    }
    challenge.id = id+1;
    await questions.insertOne(challenge);

    return res.json({ message: "Ok", id: challenge.id });
});

app.get("/challenges/:user", async function (req, res){
    let user = req.params.user;

    const challenges = await questions.find({ author: user }).toArray();

    req.session.author = user;

    return res.json({challenges});
});

app.listen(3001, function () {
    console.log('Listening on port 3001');
});