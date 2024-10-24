# Duogesto

| Service     | Duogesto                                                                                                    |
| :---------- | :---------------------------------------------------------------------------------------------------------- |
| Authors     | Stefano Alberto <@Xato>, Matteo Protopapa <@matpro>                                                         |
| Stores      | 1                                                                                                           |
| Categories  | web, misc                                                                                                   |
| Port        | HTTP 4960                                                                                                   |
| FlagIds     | store1: [username]                                                                                       |
| Checkers    | [store1](/checkers/duogesto/checker.py)                                                                     |

## Description

The application allows access to a series of quizzes and the creation of new quizzes available to other users.
Each user who creates a quiz sets a secret prize that can be accessed only by himself, his friends, and those who solve one of his quizzes.

## Vulnerabilities

### Store 1 (web, misc):
Flags are saved as the prize of a user who has no solvable quizzes (none of the options are correct).

#### Vuln 1: Author overwrite
The prize is returned based on the question's author, which is set in the `/question/:qid` API with the correct answers. The vuln is that the author is also set in the `/challenges/:user` API, leading to an overwrite of that field. This way, you can create a new challenge with a correct answer, ask for the challenges of the flag user and answer to your own challenge. This way, the answer is correct and the author is set to the one who owns the flag, revaling it as the prize.

A possible patch is to remove the line `req.session.author = user;` from the `/challenges/:user` API.

#### Vuln 2: Friend spoofing

The application allows users to add friends, these have access to the user's prize without needing to answer questions correctly.

To decide whether one user is a friend of another, this check is performed.

```
req.session.user?.friends?.includes(existingQuestion.author)
```

During registration the list of friends is set to an empty array to be saved in the database, at the same time, however, the details provided in the post are directly saved in the session, instead of the `newUser` object.

```
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
```

This makes it possible to register with an arbitrary list of friends and to gain access to the prize of any user.

To patch simply use the `newUser` object to initialize the session.

#### Vuln 2: SSRF mongoDB

The application allows images to be uploaded from a url, to do so curl is run like this.

```
let x = spawn('/usr/bin/curl', ['--max-filesize', '1M', url, '-o', filename], { cwd: `${__dirname}/files/${username}`, uid: 1000, timeout:3000});
```

The user controls both the url and filename parameters, the files are downloaded to a folder reserved for the user, and the command is executed with permissions that do not allow it to directly access files with user prizes (which contain flags).

You can exploit this command to force a query to the database and read arbitrary data. This allows obtaining the password of the user who entered the flag.

To exploit this vulnerability, the curl option `-K` or `--config` can be used, which allows the details of the request to be read from a file, thus allowing the full functionality of curl to be exploited.

In fact, by running the command passing the value `-K` as the url, it is possible to force curl to read the configuration file from the `-o` file.
Having the ability to create arbitrary files in our user's folder, it is sufficient to load the desired configuration file and then use it.

A configuration file of this type can be used to connect to the database.

```
next
url="telnet://duogesto-database:27017"
upload-file="raw.txt"
output="leak.txt"
no-buffer
```

This configuration allows you to send arbitrary bytes read from the `raw.txt` file to the database and write the response in `leak.txt`.

For example, you can request all user data by sending this bytes.

```
with open('raw.txt','wb'):
    data = b"\x67\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\xdd\x07\x00\x00\x00\x00\x00\x00\x00\x52\x00\x00\x00\x02\x66\x69\x6e\x64\x00\x06\x00\x00\x00\x75\x73\x65\x72\x73\x00\x03\x66\x69\x6c\x74\x65\x72\x00\x05\x00\x00\x00\x00\x03\x6c\x73\x69\x64\x00\x1e\x00\x00\x00\x05\x69\x64\x00\x10\x00\x00\x00\x04\x31\xdb\xaa\x5d\xd7\xab\x42\xde\xb9\xdb\x86\xf0\x88\x08\x17\xbc\x00\x02\x24\x64\x62\x00\x03\x00\x00\x00\x64\x62\x00\x00"
    f.write(data)
```



The steps to follow are:
- Load a `raw.txt` file with bytes for interaction with the database
- Upload the `-o` file with the configuration 
- Request the upload by sending `-K` as the url and a valid domain name, e.g., `example.com` as the name


## Exploits

| Store | Exploit                                                                                      |
| :---: | :------------------------------------------------------------------------------------------- |
|   1   | [author_overwrite](/exploits/duogesto/author_overwrite.py)                                   |
|   1   | [friend_spoofing](/exploits/duogesto/friend_spoofing.py)                                     |
|   1   | [curl_ssrf](/exploits/duogesto/curl_ssrf.py)                                                 |
