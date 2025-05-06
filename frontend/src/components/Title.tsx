import { useState } from "react";
import axios from "axios";

type Props = {
  setMessages: any;
  setLanguage: any;
};

function Title({ setMessages, setLanguage }: Props) {
  const [isResetting, setIsResetting] = useState(false);
  const [isClicked, setIsClicked] = useState(false); // Track if button is clicked
  const [selectedLanguage, setSelectedLanguage] = useState("hindi"); // Track selected language

  const resetConversation = async () => {
    setIsResetting(true);

    await axios
      .get("http://localhost:8000/reset", {
        headers: {
          "Content-Type": "application/json",
        },
      })
      .then((res) => {
        if (res.status == 200) {
          setMessages([]);
        }
      })
      .catch((err) => {});

    setIsResetting(false);
  };

  const handleButtonClick = () => {
    setIsClicked(!isClicked); // Toggle the clicked state
  };

  const handleLanguageChange = (language: string) => {
    setLanguage(language);
    setSelectedLanguage(language); 
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        width: "100%",
        padding: "16px",
        backgroundColor: "#1a202c",
        color: "white",
        fontWeight: "bold",
        boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
      }}
    >
      <div style={{ fontWeight: "bold" }}>Language Translator</div>
      <div>
        <button
          onClick={() => handleLanguageChange("hindi")}
          style={{
            transition: "all 0.3s",
            color: selectedLanguage === "hindi" ? "#3b82f6" : "white", // Highlight the active button
            marginRight: "16px",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => e.target.style.color = "#3b82f6"} // Blue on hover
          onMouseLeave={(e) => e.target.style.color = selectedLanguage === "hindi" ? "#3b82f6" : "white"} // Reset color or keep blue if active
        >
          Hindi
        </button>
        <button
          onClick={() => handleLanguageChange("nepali")}
          style={{
            transition: "all 0.3s",
            color: selectedLanguage === "nepali" ? "#3b82f6" : "white", // Highlight the active button
            cursor: "pointer",
          }}
          onMouseEnter={(e) => e.target.style.color = "#3b82f6"} // Blue on hover
          onMouseLeave={(e) => e.target.style.color = selectedLanguage === "nepali" ? "#3b82f6" : "white"} // Reset color or keep blue if active
        >
          Nepali
        </button>
      </div>
      <button
        onClick={() => {
          handleButtonClick();
          resetConversation();
        }} // Handle button click and reset conversation
        style={{
          transition: "all 0.3s",
          color: isClicked ? "red" : "white", // Red when clicked
          cursor: "pointer",
        }}
        onMouseEnter={(e) => e.target.style.color = "#3b82f6"} // Blue on hover
        onMouseLeave={(e) => e.target.style.color = isClicked ? "red" : "white"} // Maintain red if clicked, else reset to white
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          style={{ width: "24px", height: "24px" }}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
    </div>
  );
}

export default Title;