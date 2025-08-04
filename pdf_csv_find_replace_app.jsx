import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function FindReplaceApp() {
  const [file, setFile] = useState(null);
  const [findWord, setFindWord] = useState('');
  const [replaceWord, setReplaceWord] = useState('');
  const [downloadLink, setDownloadLink] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleReplace = async () => {
    if (!file || !findWord || !replaceWord) return alert("Please fill all fields and upload a file");

    const formData = new FormData();
    formData.append('file', file);
    formData.append('findWord', findWord);
    formData.append('replaceWord', replaceWord);

    const response = await fetch('/api/replace', {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setDownloadLink(url);
    } else {
      alert("Failed to process the file");
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Find and Replace in PDF/CSV</h1>
      <Input type="file" accept=".pdf,.csv" onChange={handleFileChange} />
      <Input
        placeholder="Word to find"
        value={findWord}
        onChange={(e) => setFindWord(e.target.value)}
      />
      <Input
        placeholder="Word to replace with"
        value={replaceWord}
        onChange={(e) => setReplaceWord(e.target.value)}
      />
      <Button onClick={handleReplace}>Replace</Button>
      {downloadLink && (
        <a
          href={downloadLink}
          download={`modified_${file.name}`}
          className="block text-blue-600 mt-4"
        >
          Download Modified File
        </a>
      )}
    </div>
  );
}
