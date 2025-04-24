import { useState } from "react";
import Title from "./Title";
import axios from "axios";
import RecordMessage from "./RecordMessage";

const Controller = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [language, setLanguage] = useState<string>("hindi");
  const [error, setError] = useState<string | null>(null);

  const showError = (message = "Something went wrong. Please try again.") => {
    setError(message);
    setTimeout(() => setError(null), 4000);
  };

  const createBlobURL = (data: any) => {
    const blob = new Blob([data], { type: "audio/mpeg" });
    return window.URL.createObjectURL(blob);
  };

  const handleStop = async (blobUrl: string) => {
    setIsLoading(true);
    console.log("Processing recorded audio...");

    try {
      const response = await fetch(blobUrl);
      const blob = await response.blob();

      if (blob.size === 0) {
        console.error("Error: Recorded blob is empty!");
        showError("Audio decoding failed. Please try recording again.");
        setIsLoading(false);
        return;
      }

      const formData = new FormData();
      formData.append("file", blob, "audio.wav");

      const { data } = await axios.post("http://localhost:8000/post-audio", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        params: { language }
      });

      const { message_decoded, english_response, hindi_translation, nepali_translation, audio_id } = data;

      if (!message_decoded) {
        showError("Failed to decode the audio message.");
        setIsLoading(false);
        return;
      }

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "me", text: message_decoded, blobUrl },
      ]);

      if (
        !english_response ||
        (language === "hindi" && !hindi_translation) ||
        (language === "nepali" && !nepali_translation)
      ) {
        showError("Translation failed. Please try again.");
        setIsLoading(false);
        return;
      }

      const audioResponse = await axios.get(`http://localhost:8000/get-audio/${audio_id}`, {
        responseType: "blob",
      });

      if (!audioResponse?.data) {
        showError("Failed to generate translated audio.");
        setIsLoading(false);
        return;
      }

      const audioUrl = createBlobURL(audioResponse.data);
      const audioElement = new Audio(audioUrl);
      audioElement.play();

      setMessages((prevMessages) => [
        ...prevMessages,
        {
          sender: "Translation",
          blobUrl: audioUrl,
          text: english_response,
          language_text: language === "hindi" ? hindi_translation : nepali_translation,
        },
      ]);
    } catch (err: any) {
      console.error("Error:", err);

      // Check if the error is from the Axios request
      if (axios.isAxiosError(err)) {
        const errorMessage =
          err.response?.data?.detail || "Something went wrong. Please try again.";
        showError(errorMessage);
      } else {
        showError("Unexpected error occurred.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen overflow-y-hidden">
      {error && (
        <div className="fixed top-5 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50">
          {error}
        </div>
      )}

      <Title setMessages={setMessages} setLanguage={setLanguage} />

      <div className="flex flex-col justify-between h-full overflow-y-scroll pb-96">
        <div className="mt-5 px-5">
          {messages.length === 0 && !isLoading && (
            <div className="text-center font-light italic mt-10">Say something...</div>
          )}

          {isLoading && (
            <div className="text-center font-light italic mt-10 animate-pulse">Gimme a few seconds...</div>
          )}

          {messages.map((audio, index) => (
            <div key={index + audio.sender} className="flex flex-col w-full mt-4 text-left">
              {audio.sender === "me" ? (
                <div className="flex justify-start w-full">
                  <div className="flex flex-col items-start p-5">
                    <p className="italic text-blue-500">{audio.sender}</p>
                    <audio src={audio.blobUrl} className="appearance-none" controls />
                    {audio.text && (
                      <p className="mt-2 w-60 h-8 text-sm text-gray-700 font-semibold text-center flex items-center justify-center bg-[#ddddddcc] p-2 rounded-tl-lg rounded-br-lg mx-auto">
                        {audio.text}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex justify-center items-center w-full">
                  <div className="flex flex-col items-start">
                    <p className="italic text-blue-500">{audio.sender}</p>
                    <audio src={audio.blobUrl} className="appearance-none" controls />
                    {audio.language_text && (
                      <p className="mt-2 w-60 h-8 text-sm text-gray-700 font-semibold text-center flex items-center justify-center bg-[#ddddddcc] p-2 rounded-tl-lg rounded-br-lg mx-auto">
                        {audio.language_text}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="fixed bottom-10 right-10 bg-gray-900 text-white p-5 rounded-lg shadow-lg w-1/3 max-h-[80vh] overflow-y-auto space-y-2">
          <p className="font-bold text-lg mb-4">CHAT RESPONSE</p>
          {messages.map((msg, index) =>
            msg.text ? (
              <div key={index} className="flex items-start bg-white text-black p-3 mt-2 rounded-lg max-w-[80%]">
                <img src={msg.sender === "me" ? "/user.png" : "/chatbot.png"} alt="Icon" className="w-8 h-8 rounded-full mr-3" />
                <div>
                  <p className="font-semibold">{msg.sender === "me" ? "User:" : "Chatbot:"}</p>
                  <p className={msg.sender === "me" ? "text-sm" : "text-sm italic"}>{msg.text}</p>
                </div>
              </div>
            ) : null
          )}
        </div>

        <div className="fixed bottom-0 w-full py-5 text-center">
          <div className="flex justify-center items-center w-full">
            <RecordMessage handleStop={handleStop} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Controller;
