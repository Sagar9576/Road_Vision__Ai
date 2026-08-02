const fs = require("fs");
const express = require("express");
const cors = require("cors");
const app = express();
app.use(cors());

app.get("/", (req, res) => {
    res.send("Backend Working");
});

app.get("/status", (req, res) => {

    const data = fs.readFileSync(
        "../ai_status.json",
        "utf8"
    );

    res.json(JSON.parse(data));
});

app.listen(5000, () => {
    console.log("Server running on port 5000");
});