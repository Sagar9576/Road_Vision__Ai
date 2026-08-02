import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000";

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`${API_URL}/status`);
        setData(response.data);
      } catch (error) {
        console.error("Backend Error:", error);
      }
    };

    fetchData();

    const interval = setInterval(fetchData, 2000);

    return () => clearInterval(interval);
  }, []);

  if (!data) {
    return (
      <div className="container">
        <h1 className="title">🚗 AI Driving Copilot</h1>
        <h2 style={{ textAlign: "center" }}>
          Connecting to Backend...
        </h2>
      </div>
    );
  }

  return (
    <div className="container">

      <h1 className="title">🚗 AI Driving Copilot</h1>

      <p className="subtitle">
        Real-Time Autonomous Vehicle Monitoring
      </p>

      <h3 style={{ textAlign: "center" }}>
        🕒 {new Date().toLocaleTimeString()}
      </h3>

      <div className="grid">

        <div className="advice-card">
          <h2>🤖 AI Advice</h2>
          <p>{data.ai_advice}</p>
        </div>

        <div className="online">
          🟢 System Status: ONLINE
        </div>

        <div className="card">
          <h3>🚗 Cars</h3>
          <p>{data.cars}</p>
        </div>

        <div className="card">
          <h3>🚶 People</h3>
          <p>{data.people}</p>
        </div>

        <div className="card">
          <h3>🚦 Traffic</h3>
          <p
            style={{
              color:
                data.traffic === "HIGH"
                  ? "red"
                  : data.traffic === "MEDIUM"
                  ? "orange"
                  : "lime",
            }}
          >
            {data.traffic}
          </p>
        </div>

        <div className="card">
          <h3>⚠️ Risk</h3>
          <p
            style={{
              color:
                data.risk === "HIGH"
                  ? "red"
                  : data.risk === "MEDIUM"
                  ? "orange"
                  : "lime",
            }}
          >
            {data.risk}
          </p>
        </div>

        <div className="card">
          <h3>🛣️ Lane</h3>
          <p>{data.lane_status}</p>
        </div>

        <div className="card">
          <h3>🛑 Sign</h3>
          <p>{data.sign}</p>
        </div>

        <div className="card">
          <h3>🎯 Action</h3>
          <p>{data.action}</p>
        </div>

        <div className="card">
          <h3>⭐ Score</h3>

          <p>{data.score}</p>

          <div className="progress">
            <div
              className="fill"
              style={{ width: `${data.score}%` }}
            ></div>
          </div>
        </div>

      </div>

    </div>
  );
}

export default App;