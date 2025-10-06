import axios from 'axios';
import { useRef, useState } from 'react';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioURL, setAudioURL] = useState('');
  const [transcriptions, setTranscriptions] = useState(null);
  const [groundTruth, setGroundTruth] = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState([]);
  const [showRecords, setShowRecords] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Start recording
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Try to use WAV format if supported, otherwise use webm
    const mimeType = MediaRecorder.isTypeSupported('audio/wav') 
      ? 'audio/wav' 
      : MediaRecorder.isTypeSupported('audio/webm') 
      ? 'audio/webm' 
      : '';
    
    mediaRecorderRef.current = new MediaRecorder(stream, {
      mimeType: mimeType || undefined
    });
    
    audioChunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      audioChunksRef.current.push(event.data);
    };

    mediaRecorderRef.current.onstop = async () => {
      // Create blob with the actual recorded format
      const recordedMimeType = mediaRecorderRef.current.mimeType;
      const audioBlob = new Blob(audioChunksRef.current, { type: recordedMimeType });
      
      setAudioBlob(audioBlob);
      setAudioURL(URL.createObjectURL(audioBlob));
      stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
    setTranscriptions(null);
    setEvaluation(null);
    setGroundTruth('');
  } catch (error) {
    console.error('Error accessing microphone:', error);
    alert('Error accessing microphone. Please check permissions.');
  }
};

// Stop recording
const stopRecording = () => {
  if (mediaRecorderRef.current && isRecording) {
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  }
};

// Send audio to backend for transcription
const transcribeAudio = async () => {
  if (!audioBlob) {
    alert('Please record audio first!');
    return;
  }

  setLoading(true);
  const formData = new FormData();
  
  // Use appropriate filename extension based on blob type
  const extension = audioBlob.type.includes('webm') ? 'webm' : 'wav';
  const filename = `recording_test.${extension}`;
  
  formData.append('file', audioBlob, filename);

  try {
    const response = await axios.post(`${API_BASE_URL}/transcribe`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    setTranscriptions({
      ...response.data,
      filename
    });
  } catch (error) {
    console.error('Error transcribing audio:', error);
    alert('Error transcribing audio. Make sure the backend is running!');
  } finally {
    setLoading(false);
  }
};

// Submit ground truth and evaluate
const submitEvaluation = async () => {
  if (!groundTruth.trim()) {
    alert('Please enter the correct transcription!');
    return;
  }

  if (!transcriptions) {
    alert('Please transcribe audio first!');
    return;
  }

  setLoading(true);

  const evalData = {
    audio_filename: transcriptions.filename,
    whisper_output: transcriptions.whisper_output,
    wav2vec2_output: transcriptions.wav2vec2_output,
    ground_truth: groundTruth,
    whisper_latency: transcriptions.whisper_latency,
    wav2vec2_latency: transcriptions.wav2vec2_latency
  };

  try {
    const response = await axios.post(`${API_BASE_URL}/evaluate`, evalData);
    setEvaluation(response.data);
  } catch (error) {
    console.error('Error evaluating transcriptions:', error);
    alert('Error evaluating transcriptions!');
  } finally {
    setLoading(false);
  }
};

  // Fetch all records
  const fetchRecords = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/records`);
      setRecords(response.data);
      setShowRecords(true);
    } catch (error) {
      console.error('Error fetching records:', error);
    }
  };

  // Delete record
  const deleteRecord = async (recordId) => {
    if (!window.confirm('Are you sure you want to delete this record?')) return;

    try {
      await axios.delete(`${API_BASE_URL}/records/${recordId}`);
      fetchRecords();
    } catch (error) {
      console.error('Error deleting record:', error);
    }
  };

  // Reset everything
  const resetAll = () => {
    setAudioBlob(null);
    setAudioURL('');
    setTranscriptions(null);
    setGroundTruth('');
    setEvaluation(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎙️ Speech-to-Text Model Comparison</h1>
        <p>Compare Whisper vs Wav2Vec2 models</p>
      </header>

      <div className="container">
        {/* Recording Section */}
        <div className="card">
          <h2>📝 Step 1: Record Audio</h2>
          <div className="button-group">
            <button 
              onClick={startRecording} 
              disabled={isRecording}
              className="btn btn-primary"
            >
              {isRecording ? '🔴 Recording...' : '🎤 Start Recording'}
            </button>
            <button 
              onClick={stopRecording} 
              disabled={!isRecording}
              className="btn btn-secondary"
            >
              ⏹️ Stop Recording
            </button>
            <button 
              onClick={resetAll} 
              className="btn btn-danger"
            >
              🔄 Reset
            </button>
          </div>

          {audioURL && (
            <div className="audio-player">
              <audio controls src={audioURL}></audio>
              <button 
                onClick={transcribeAudio} 
                disabled={loading}
                className="btn btn-success"
              >
                {loading ? '⏳ Transcribing...' : '🚀 Transcribe Audio'}
              </button>
            </div>
          )}
        </div>

        {/* Transcription Results */}
        {transcriptions && (
          <>
            <div className="results-container">
              <div className="result-card whisper">
                <h3>🤖 Whisper Model</h3>
                <div className="transcription-text">
                  {transcriptions.whisper_output}
                </div>
                <div className="latency">
                  ⏱️ Latency: <strong>{transcriptions.whisper_latency}s</strong>
                </div>
              </div>

              <div className="result-card wav2vec2">
                <h3>🤖 Wav2Vec2 Model</h3>
                <div className="transcription-text">
                  {transcriptions.wav2vec2_output}
                </div>
                <div className="latency">
                  ⏱️ Latency: <strong>{transcriptions.wav2vec2_latency}s</strong>
                </div>
              </div>
            </div>

            {/* Ground Truth Input */}
            <div className="card">
              <h2>✅ Step 2: Enter Correct Transcription</h2>
              <textarea
                value={groundTruth}
                onChange={(e) => setGroundTruth(e.target.value)}
                placeholder="Type the correct transcription here..."
                rows="4"
                className="ground-truth-input"
              />
              <button 
                onClick={submitEvaluation} 
                disabled={loading || !groundTruth.trim()}
                className="btn btn-success"
              >
                {loading ? '⏳ Evaluating...' : '📊 Evaluate Models'}
              </button>
            </div>
          </>
        )}

        {/* Evaluation Results */}
        {evaluation && (
          <div className="card evaluation-results">
            <h2>📊 Evaluation Results</h2>
            <div className="results-grid">
              <div className="metric-card">
                <h4>Whisper Accuracy</h4>
                <div className="metric-value">{evaluation.whisper_accuracy.toFixed(2)}%</div>
                <div className="metric-detail">WER: {evaluation.whisper_wer.toFixed(4)}</div>
              </div>
              <div className="metric-card">
                <h4>Wav2Vec2 Accuracy</h4>
                <div className="metric-value">{evaluation.wav2vec2_accuracy.toFixed(2)}%</div>
                <div className="metric-detail">WER: {evaluation.wav2vec2_wer.toFixed(4)}</div>
              </div>
            </div>
            <div className="winner">
              {evaluation.whisper_accuracy > evaluation.wav2vec2_accuracy 
                ? '🏆 Whisper wins!' 
                : evaluation.wav2vec2_accuracy > evaluation.whisper_accuracy
                ? '🏆 Wav2Vec2 wins!'
                : '🤝 It\'s a tie!'}
            </div>
            <div className="success-message">✅ {evaluation.message}</div>
          </div>
        )}

        {/* View Records Button */}
        <div className="card">
          <button onClick={fetchRecords} className="btn btn-info">
            📋 View All Records
          </button>
        </div>

        {/* Records Table */}
        {showRecords && records.length > 0 && (
          <div className="card">
            <h2>📋 Transcription History</h2>
            <div className="table-container">
              <table className="records-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>Whisper Output</th>
                    <th>Wav2Vec2 Output</th>
                    <th>Ground Truth</th>
                    <th>Whisper Acc</th>
                    <th>Wav2Vec2 Acc</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map(record => (
                    <tr key={record.id}>
                      <td>{record.id}</td>
                      <td>{new Date(record.created_at).toLocaleDateString()}</td>
                      <td className="truncate">{record.whisper_output}</td>
                      <td className="truncate">{record.wav2vec2_output}</td>
                      <td className="truncate">{record.ground_truth}</td>
                      <td>{record.whisper_accuracy}%</td>
                      <td>{record.wav2vec2_accuracy}%</td>
                      <td>
                        <button 
                          onClick={() => deleteRecord(record.id)}
                          className="btn-delete"
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;