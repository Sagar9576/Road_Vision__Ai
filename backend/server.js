const fs = require("fs");
const path = require("path");
const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());

app.get("/", (req, res) => {
    res.send("Backend Working");
});

app.get("/status", (req, res) => {

    const filePath = path.join(__dirname, "..", "ai_status.json");

    const data = fs.readFileSync(filePath, "utf8");

    res.json(JSON.parse(data));
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});