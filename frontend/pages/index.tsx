import Head from 'next/head';
import Image from 'next/image';
import axios from 'axios';
import React, { useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
    const [files, setFiles] = useState<FileList | null>(null);
    const [tool, setTool] = useState("merge");
    const [jobId, setJobId] = useState("");
    const [status, setStatus] = useState("");
    const [downloadUrl, setDownloadUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const pollStatus = async (id: string) => {
        try {
            const res = await axios.get(`${API_URL}/jobs/${id}`);
            const jobStatus = res.data.status;
            setStatus(jobStatus);

            if (jobStatus === 'completed') {
                setLoading(false);
                setDownloadUrl(`${API_URL}/jobs/${id}/result`);
            } else if (jobStatus === 'failed') {
                setLoading(false);
                setError("Job failed to process.");
            } else {
                // Still processing, poll again in 1s
                setTimeout(() => pollStatus(id), 1000);
            }
        } catch (err) {
            console.error(err);
            setLoading(false);
            setError("Error checking status");
        }
    };

    const handleUpload = async () => {
        if (!files || files.length === 0) return;
        setLoading(true);
        setStatus("uploading");
        setError("");
        setDownloadUrl("");
        setJobId("");

        const formData = new FormData();
        formData.append("tool", tool);
        formData.append("params", JSON.stringify({})); // Add actual params UI later

        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        try {
            const res = await axios.post(`${API_URL}/jobs`, formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });
            const id = res.data.job_id;
            setJobId(id);
            setStatus("queued");
            // Start polling
            pollStatus(id);
        } catch (err) {
            console.error(err);
            setLoading(false);
            setError("Upload failed");
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white font-sans selection:bg-pink-500 selection:text-white">
            <Head>
                <title>PDFsimple – Smart Document Workspace</title>
                <meta name="description" content="Merge, split, compress, and convert PDFs with AI-powered speed." />
            </Head>

            {/* Navbar */}
            <nav className="w-full py-6 px-8 flex justify-between items-center max-w-7xl mx-auto">
                <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-violet-500">
                    PDFsimple
                </div>
                <div className="space-x-6 text-sm font-medium text-gray-300">
                    <a href="#" className="hover:text-white transition">Tools</a>
                    <a href="#" className="hover:text-white transition">Pricing</a>
                    <a href="#" className="hover:text-white transition">Login</a>
                </div>
            </nav>

            {/* Hero Section */}
            <main className="flex flex-col items-center justify-center p-4 mt-10">
                <div className="text-center max-w-3xl mb-12">
                    <h1 className="text-5xl md:text-7xl font-extrabold mb-6 tracking-tight">
                        Master your <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500">Documents</span>
                    </h1>
                    <p className="text-xl text-gray-400 mb-8 leading-relaxed">
                        The all-in-one workspace to merge, split, compress, and convert PDFs. <br className="hidden md:block" />
                        Simple, fast, and secure.
                    </p>
                </div>

                {/* Tool Card / Upload Area */}
                <div className="w-full max-w-2xl bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 p-8 rounded-2xl shadow-2xl relative overflow-hidden group">
                    {/* Decorative gradient blob */}
                    <div className="absolute -top-20 -right-20 w-64 h-64 bg-purple-600/20 rounded-full blur-3xl group-hover:bg-purple-600/30 transition duration-1000"></div>

                    <div className="relative z-10">
                        <div className="mb-8">
                            <label className="block text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">Choose Action</label>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {['merge', 'split', 'compress', 'convert'].map((t) => (
                                    <button
                                        key={t}
                                        onClick={() => setTool(t)}
                                        className={`py-3 px-4 rounded-xl text-sm font-medium transition-all duration-300 border ${tool === t
                                                ? 'bg-gradient-to-br from-purple-600 to-indigo-600 border-transparent text-white shadow-lg scale-105'
                                                : 'bg-gray-700/50 border-gray-600 text-gray-400 hover:bg-gray-700 hover:text-white'
                                            }`}
                                    >
                                        {t.charAt(0).toUpperCase() + t.slice(1)}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="mb-8">
                            <label className="block text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">Upload Files</label>
                            <div className="relative group/upload">
                                <input
                                    type="file"
                                    multiple
                                    onChange={(e) => setFiles(e.target.files)}
                                    className="block w-full text-sm text-gray-400
                                      file:mr-4 file:py-3 file:px-6
                                      file:rounded-full file:border-0
                                      file:text-sm file:font-semibold
                                      file:bg-gray-700 file:text-purple-400
                                      hover:file:bg-gray-600
                                      cursor-pointer border border-gray-600 rounded-xl bg-gray-900/50"
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                {error}
                            </div>
                        )}

                        {status && (
                            <div className="mb-6">
                                <div className="flex justify-between text-sm mb-2 text-gray-400">
                                    <span>Status</span>
                                    <span className="text-white font-medium capitalize">{status}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className={`h-2 rounded-full transition-all duration-500 ${status === 'completed' ? 'bg-green-500 w-full' :
                                                status === 'failed' ? 'bg-red-500 w-full' :
                                                    'bg-purple-500 w-2/3 animate-pulse'
                                            }`}
                                    ></div>
                                </div>
                            </div>
                        )}

                        {downloadUrl ? (
                            <a
                                href={downloadUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="block w-full text-center py-4 rounded-xl font-bold text-lg bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg hover:shadow-green-500/25 hover:-translate-y-1 transition-all duration-300"
                            >
                                Download Your File
                            </a>
                        ) : (
                            <button
                                onClick={handleUpload}
                                disabled={loading || !files}
                                className={`w-full py-4 rounded-xl font-bold text-lg shadow-lg transition-all duration-300 ${loading || !files
                                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                        : 'bg-white text-gray-900 hover:bg-gray-100 hover:shadow-white/10 hover:-translate-y-1'
                                    }`}
                            >
                                {loading ? (
                                    <span className="flex items-center justify-center">
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Processing...
                                    </span>
                                ) : 'Start Magic ✨'}
                            </button>
                        )}
                    </div>
                </div>

                {/* Footer / Trust */}
                <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center text-gray-500 text-sm">
                    <div>🔒 256-bit Encryption</div>
                    <div>⚡ Lightning Fast</div>
                    <div>📂 Auto-deleted in 2h</div>
                    <div>✨ AI-Ready</div>
                </div>
            </main>
        </div>
    );
}
