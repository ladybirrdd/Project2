import { ReactMediaRecorder } from "react-media-recorder";
import RecordIcon from "./RecordIcon";

type Props = {
  handleStop: any;
};

const RecordMessage = ({ handleStop }: Props) => {
  return (
    <ReactMediaRecorder
      audio
      onStop={(blobUrl) => {
        console.log("Recording stopped, resetting microphone...");

        navigator.mediaDevices.getUserMedia({ audio: true })
          .then((stream) => {
            stream.getTracks().forEach((track) => track.stop());
          })
          .catch((err) => console.error("Microphone reset error:", err));

        handleStop(blobUrl);
      }}
      render={({ status, startRecording, stopRecording }) => (
        <div className="mt-2">
          <button
            onMouseDown={() => {
              console.log("Recording started...");
              startRecording();
            }}
            onMouseUp={() => {
              console.log("Recording stopped.");
              stopRecording();
            }}
            className="bg-gray-900 p-4 rounded-full"
          >
            <RecordIcon
              classText={
                status === "recording"
                  ? "animate-pulse text-red-500"
                  : "text-sky-500"
              }
            />
          </button>
          <p className="mt-0 text-gray-900 font-medium">{status}</p>
        </div>
      )}
    />
  );
};

export default RecordMessage;
