
import React, { useState } from 'react';

function SubmissionForm() {
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('description', description);
    if (file) {
      formData.append('file', file);
    }

    try {
      const response = await fetch('http://localhost:5001/submit', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setMessage(`Success: ${result.message}`);
        setDescription('');
        setFile(null);
        // Clear the file input
        event.target.reset();
      } else {
        setMessage(`Error: ${result.error}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.toString()}`);
    }
  };

  return (
    <div className="submission-form-container">
      <h2>Citizen's Voice Submission</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the issue..."
          rows="5"
        />
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit">Submit Evidence</button>
      </form>
      {message && <p className="submission-message">{message}</p>}
    </div>
  );
}

export default SubmissionForm;
