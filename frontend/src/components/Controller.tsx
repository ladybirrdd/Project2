import { useState } from "react";
import Title from "./Title";
import axios from "axios";
import RecordMessage from "./RecordMessage";

interface Message {
  sender: "me" | "Translation";
  text: string;
  language_text?: string;
  blobUrl: string | null;
}

const Controller = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [language, setLanguage] = useState<string>("hindi");
  const [error, setError] = useState<string | null>(null);

  const showError = (message = "Something went wrong. Please try again.") => {
    setError(message);
    setTimeout(() => setError(null), 4000);
  };

  const createBlobURL = (data: Blob) => window.URL.createObjectURL(data);

  const handleStop = async (blobUrl: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(blobUrl);
      const blob = await response.blob();

      if (blob.size === 0) {
        showError("Empty recording. Please try again.");
        return;
      }

      const formData = new FormData();
      formData.append("file", blob, "audio.wav");

      const decodeRes = await axios.post("http://localhost:8000/decode-audio", formData);
      const message_decoded = decodeRes.data.message_decoded;

      setMessages(prev => [...prev, { sender: "me", text: message_decoded, blobUrl }]);

      const responseRes = await axios.post("http://localhost:8000/generate-response", {
        message: message_decoded,
        language
      });

      const { english_response, translation } = responseRes.data;

      const translationMessage: Message = {
        sender: "Translation",
        text: english_response,
        language_text: translation,
        blobUrl: null
      };

      setMessages(prev => [...prev, translationMessage]);

      const audioRes = await axios.post("http://localhost:8000/generate-audio", { translation });
      const audio_id = audioRes.data.audio_id;

      const audioFile = await axios.get(`http://localhost:8000/get-audio/${audio_id}`, {
        responseType: "blob"
      });

      const audioUrl = createBlobURL(audioFile.data);
      const audioElement = new Audio(audioUrl);
      audioElement.play();

      setMessages(prev =>
        prev.map(msg =>
          msg.text === english_response ? { ...msg, blobUrl: audioUrl } : msg
        )
      );
    } catch (err: any) {
      console.error(err);
      if (axios.isAxiosError(err)) {
        showError(err.response?.data?.detail || "Something went wrong.");
      } else {
        showError("Unexpected error.");
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
            <div key={`${audio.sender}-${index}`} className="flex flex-col w-full mt-4 text-left">
              {audio.sender === "me" ? (
                <div className="flex justify-start w-full">
                  <div className="flex flex-col items-start p-5">
                    <p className="italic text-blue-500">{audio.sender}</p>
                    {audio.blobUrl && <audio src={audio.blobUrl} controls />}
                    <p className="mt-2 max-w-[240px] text-sm text-gray-700 font-semibold text-center break-words bg-[#ddddddcc] p-2 rounded-tl-lg rounded-br-lg mx-auto">
                      {audio.text}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex justify-center items-center w-full">
                  <div className="flex flex-col items-start">
                    <p className="italic text-blue-500">{audio.sender}</p>
                    {audio.blobUrl && <audio src={audio.blobUrl} controls />}
                    <p className="mt-2 max-w-[240px] text-sm text-gray-700 font-semibold text-center break-words bg-[#ddddddcc] p-2 rounded-tl-lg rounded-br-lg mx-auto">
                      {audio.language_text || audio.text}
                    </p>
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
              <div key={`${msg.sender}-${index}`} className="flex items-start bg-white text-black p-3 mt-2 rounded-lg max-w-[80%]">
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

