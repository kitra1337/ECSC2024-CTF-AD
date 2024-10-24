// init-mongo.js
db = db.getSiblingDB('db'); // Replace with your database name

db.createCollection('users'); // Replace with your collection name
// Add more collections as needed

db.createCollection('questions');
db.questions.insertMany([
    { id: 1, image: "questions/quiz1.webp", question: "What does the guy want to say?", answers: ["The food is very nice", "There is a mosquito around him", "There is a bad smell"], correct: ["The food is very nice"], author: "" },
    { id: 2, image: "questions/quiz2.gif", question: "What does this gesture mean?", answers: ['"What do you want?"', '"Give me some money"', '"Come closer"'], correct: ["What do you want?"], author: "" },
    { id: 3, image: "questions/quiz3.gif", question: "What do you want to say with this?", answers: ["This is perfect", "I want to kiss you", "The chef is in love"], correct: ["This is perfect"], author: "" },
    { id: 4, image: "questions/quiz4.webp", question: "In which context you can do this?", answers: ["When you don't care", "When your chin itches", "When you want fresh air"], correct: ["When you don't care"], author: "" },
    { id: 5, image: "questions/quiz5.webp", question: "What do you understand?", answers: ["The guy approves", "The guy want to order three drinks", "The guy is drunk"], correct: ["The guy approves"], author: "" },
]);
