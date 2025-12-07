import Head from 'next/head';
import axios from 'axios';
import React, { useState, useEffect } from 'react';
import {
    CloudArrowUpIcon,
    DocumentDuplicateIcon,
    ScissorsIcon,
    ArrowsPointingInIcon,
    ArrowPathIcon,
    CheckCircleIcon,
    XCircleIcon,
    ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const tools = [
    { id: 'merge', name: 'Merge', icon: DocumentDuplicateIcon, desc: 'Combine multiple PDFs into one.' },
    { id: 'split', name: 'Split', icon: ScissorsIcon, desc: 'Separate PDF pages instantly.' },
    { id: 'compress', name: 'Compress', icon: ArrowsPointingInIcon, desc: 'Reduce file size, keep quality.' },
    { id: 'convert', name: 'Convert', icon: ArrowPathIcon, desc: 'Transform PDFs to other formats.' },
    { id: 'ocr', name: 'OCR', icon: DocumentDuplicateIcon, desc: 'Make scanned PDFs searchable.' },
    { id: 'pdf_to_pptx', name: 'PDF→PPTX', icon: ArrowPathIcon, desc: 'Convert PDF to PowerPoint.' },
    { id: 'pdf_to_xlsx', name: 'PDF→XLSX', icon: ArrowPathIcon, desc: 'Extract tables to Excel.' },
    { id: 'pdf_to_html', name: 'PDF→HTML', icon: ArrowPathIcon, desc: 'Convert PDF to HTML.' },
    { id: 'images_to_pdf', name: 'Images→PDF', icon: ArrowPathIcon, desc: 'Combine images into PDF.' },
    { id: 'watermark', name: 'Watermark', icon: DocumentDuplicateIcon, desc: 'Add text or image watermarks.' },
    { id: 'page_numbers', name: 'Page Numbers', icon: DocumentDuplicateIcon, desc: 'Add page numbering.' },
    { id: 'rotate', name: 'Rotate', icon: ArrowPathIcon, desc: 'Rotate PDF pages.' },
    { id: 'metadata', name: 'Metadata', icon: DocumentDuplicateIcon, desc: 'Edit PDF metadata.' },
    { id: 'protect', name: 'Protect', icon: DocumentDuplicateIcon, desc: 'Password protect PDFs.' },
    { id: 'unlock', name: 'Unlock', icon: DocumentDuplicateIcon, desc: 'Remove PDF passwords.' },
];

export default function Home() {
    const [files, setFiles] = useState<FileList | null>(null);
    const [tool, setTool] = useState("merge");
    const [params, setParams] = useState<any>({});
    const [jobId, setJobId] = useState("");
    const [status, setStatus] = useState("");
    const [downloadUrl, setDownloadUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [jobStats, setJobStats] = useState<any>({});

    // Batch State
    const [batchJobs, setBatchJobs] = useState<any[]>([]);
    const [isBatch, setIsBatch] = useState(false);

    const activeTool = tools.find(t => t.id === tool) || tools[0];

    useEffect(() => {
        // Reset state when tool changes
        setFiles(null);
        setJobId("");
        setBatchJobs([]);
        setIsBatch(false);
        setStatus("");
        setDownloadUrl("");
        setError("");
        setLoading(false);

        // Default params
        if (tool === 'convert') setParams({ target_format: 'pdf' });
        else if (tool === 'compress') setParams({ level: 'medium' });
        else if (tool === 'pdf_to_pptx') setParams({ dpi: 150, title: 'PDF Presentation' });
        else if (tool === 'pdf_to_xlsx') setParams({ extract_text: false });
        else if (tool === 'pdf_to_html') setParams({ mode: 'text', dpi: 150 });
        else if (tool === 'images_to_pdf') setParams({ orientation: 'auto' });
        else if (tool === 'watermark') setParams({ watermark_type: 'text', position: 'center', opacity: 0.3, rotation: 45, font_size: 60 });
        else if (tool === 'page_numbers') setParams({ position: 'bottomright', format: '{number}' });
        else if (tool === 'rotate') setParams({ angle: 90, pages: 'all' });
        else if (tool === 'metadata') setParams({ action: 'set' });
        else if (tool === 'protect') setParams({ password: '' });
        else if (tool === 'unlock') setParams({ password: '' });
        else setParams({});
    }, [tool]);

    const pollStatus = async (id: string, isBatchItem = false) => {
        try {
            const res = await axios.get(`${API_URL}/jobs/${id}`);
            const jobStatus = res.data.status;

            if (isBatchItem) {
                // Update item in batchJobs
                setBatchJobs(prev => prev.map(j => {
                    if (j.job_id === id) {
                        const updated = { ...j, status: jobStatus };
                        if (jobStatus === 'completed') updated.downloadUrl = `${API_URL}/jobs/${id}/result`;
                        if (jobStatus === 'failed') updated.error = "Failed";
                        return updated;
                    }
                    return j;
                }));

                if (jobStatus !== 'completed' && jobStatus !== 'failed') {
                    setTimeout(() => pollStatus(id, true), 2000);
                }
                return;
            }

            setStatus(jobStatus);
            if (jobStatus === 'completed') {
                setLoading(false);
                setDownloadUrl(`${API_URL}/jobs/${id}/result`);

                // If compress tool, we have stats in res.data.output
                if (tool === 'compress' && res.data.output && typeof res.data.output === 'object') {
                    const { original_size, compressed_size } = res.data.output;
                    const saved = original_size > 0 ? ((original_size - compressed_size) / original_size * 100).toFixed(0) : 0;
                    setJobStats({ original_size, compressed_size, saved_percent: saved });
                }
            } else if (jobStatus === 'failed') {
                setLoading(false);
                setError("Job failed to process.");
            } else {
                setTimeout(() => pollStatus(id), 1000);
            }
        } catch (err) {
            console.error(err);
            if (!isBatchItem) {
                setLoading(false);
                setError("Error checking status");
            }
        }
    };

    const handleUpload = async () => {
        if (!files || files.length === 0) return;
        setLoading(true);
        setStatus("uploading");
        setError("");
        setDownloadUrl("");
        setJobId("");
        setBatchJobs([]);

        // Determine if batch
        const _isBatch = files.length > 1 && tool !== 'merge';
        setIsBatch(_isBatch);

        const formData = new FormData();
        formData.append("tool", tool);
        formData.append("params", JSON.stringify(params));

        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        try {
            const endpoint = _isBatch ? `${API_URL}/jobs/batch` : `${API_URL}/jobs`;
            const res = await axios.post(endpoint, formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            if (_isBatch) {
                setLoading(false); // We show list immediately
                const jobs = res.data; // Array of {job_id, status, filename, error?}
                setBatchJobs(jobs);

                // Start polling for each queued job
                jobs.forEach((j: any) => {
                    if (j.job_id && (j.status === 'queued' || j.status === 'processing')) {
                        pollStatus(j.job_id, true);
                    }
                });

            } else {
                const id = res.data.job_id;
                setJobId(id);
                setStatus("queued");
                pollStatus(id);
            }

        } catch (err: any) {
            console.error(err);
            setLoading(false);
            if (err.response && err.response.data && err.response.data.error) {
                setError(err.response.data.error);
            } else {
                setError("Upload failed. Please try again.");
            }
            if (err.response && err.response.status === 429) {
                setError("Rate limit exceeded. Please wait a moment.");
            }
        }
    };

    return (
        <div className="min-h-screen bg-[#0f172a] overflow-x-hidden selection:bg-violet-500 selection:text-white">
            <Head>
                <title>PDFsimple – Ultimate PDF Tools</title>
                <meta name="description" content="Merge, split, compress, and convert PDFs with AI-powered speed." />
            </Head>

            {/* Background Gradients */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-violet-600/20 rounded-full blur-[120px] animate-pulse"></div>
                <div className="absolute top-[20%] right-[-10%] w-[35%] h-[35%] bg-fuchsia-600/20 rounded-full blur-[100px] animate-pulse delay-700"></div>
                <div className="absolute bottom-[-10%] left-[20%] w-[30%] h-[30%] bg-cyan-600/20 rounded-full blur-[100px] animate-pulse delay-1000"></div>
            </div>

            <div className="relative z-10 flex flex-col min-h-screen">
                {/* Navbar */}
                <nav className="w-full py-6 px-6 md:px-12 flex justify-between items-center backdrop-blur-sm border-b border-white/5">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-violet-500/20">
                            P
                        </div>
                        <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            PDFsimple
                        </span>
                    </div>
                </nav>

                <main className="flex-grow container mx-auto px-4 py-12 md:py-20 flex flex-col items-center">

                    {/* Hero Text */}
                    <div className="text-center max-w-4xl mb-16">
                        <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-tight">
                            Simplify your <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 animate-gradient-x">
                                Document Workflow
                            </span>
                        </h1>
                        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto">
                            The most powerful, secure, and blazing fast PDF tools on the web.
                            Process your documents with locally-powered privacy principles.
                        </p>
                    </div>

                    {/* Main Interface Component */}
                    <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8">

                        {/* Sidebar / Tool Selection */}
                        <div className="lg:col-span-4 space-y-4">
                            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-2xl">
                                <h3 className="text-gray-400 text-xs font-bold uppercase tracking-widest mb-4">Select Tool</h3>
                                <div className="space-y-3">
                                    {tools.map((t) => (
                                        <button
                                            key={t.id}
                                            onClick={() => setTool(t.id)}
                                            className={`w-full flex items-center p-4 rounded-2xl transition-all duration-300 group ${tool === t.id
                                                ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/25 ring-1 ring-white/20'
                                                : 'bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-transparent hover:border-white/10'
                                                }`}
                                        >
                                            <div className={`p-2 rounded-lg mr-4 ${tool === t.id ? 'bg-white/20' : 'bg-gray-800 group-hover:bg-gray-700'}`}>
                                                <t.icon className="w-6 h-6" />
                                            </div>
                                            <div className="text-left">
                                                <div className="font-semibold">{t.name}</div>
                                                <div className={`text-xs ${tool === t.id ? 'text-violet-200' : 'text-gray-500'}`}>{t.desc}</div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Workspace Area */}
                        <div className="lg:col-span-8">
                            <div className="h-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 flex flex-col items-center justify-center relative overflow-hidden shadow-2xl">

                                {/* Header for Workspace */}
                                <div className="w-full flex justify-between items-center mb-8 border-b border-white/5 pb-6">
                                    <div className="flex items-center gap-3">
                                        <activeTool.icon className="w-8 h-8 text-violet-400" />
                                        <h2 className="text-2xl font-bold text-white">{activeTool.name} PDF</h2>
                                    </div>
                                    <div className="text-sm text-gray-500 font-medium">
                                        {status ? `Status: ${status}` : 'Ready to start'}
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="w-full max-w-md space-y-6">

                                    {/* Tool Options - Convert */}
                                    {tool === 'convert' && (
                                        <div className="mb-8 w-full">
                                            <h3 className="text-center text-white font-bold text-xl mb-6">Convert To</h3>
                                            <div className="flex justify-center gap-4">
                                                {[
                                                    { id: 'pdf', label: 'PDF', icon: DocumentDuplicateIcon },
                                                    { id: 'docx', label: 'Word', icon: DocumentDuplicateIcon },
                                                    { id: 'jpg', label: 'JPG', icon: CloudArrowUpIcon }
                                                ].map((fmt) => (
                                                    <button
                                                        key={fmt.id}
                                                        onClick={() => setParams({ ...params, target_format: fmt.id })}
                                                        className={`flex flex-col items-center justify-center w-24 h-24 rounded-2xl border-2 transition-all duration-300 ${params.target_format === fmt.id
                                                            ? 'bg-violet-600 border-violet-500 text-white shadow-lg shadow-violet-500/40 scale-105'
                                                            : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10 hover:border-white/30'
                                                            }`}
                                                    >
                                                        <span className="font-bold text-lg">{fmt.label}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - PDF to PPTX */}
                                    {tool === 'pdf_to_pptx' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">PDF to PowerPoint</h3>
                                            <div className="space-y-3">
                                                <div>
                                                    <label className="text-white text-sm font-medium">DPI:</label>
                                                    <input
                                                        type="number"
                                                        placeholder="150"
                                                        value={params.dpi || 150}
                                                        onChange={(e) => setParams({ ...params, dpi: parseInt(e.target.value) })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="text-white text-sm font-medium">Presentation Title:</label>
                                                    <input
                                                        type="text"
                                                        placeholder="PDF Presentation"
                                                        onChange={(e) => setParams({ ...params, title: e.target.value })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - PDF to XLSX */}
                                    {tool === 'pdf_to_xlsx' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">PDF to Excel</h3>
                                            <label className="flex items-center gap-3 text-white cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    checked={params.extract_text || false}
                                                    onChange={(e) => setParams({ ...params, extract_text: e.target.checked })}
                                                    className="w-4 h-4"
                                                />
                                                <span className="text-sm">Also extract text content</span>
                                            </label>
                                        </div>
                                    )}

                                    {/* Tool Options - PDF to HTML */}
                                    {tool === 'pdf_to_html' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">PDF to HTML</h3>
                                            <div>
                                                <label className="text-white text-sm font-medium">Mode:</label>
                                                <select
                                                    value={params.mode || 'text'}
                                                    onChange={(e) => setParams({ ...params, mode: e.target.value })}
                                                    className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                >
                                                    <option value="text">Text (searchable)</option>
                                                    <option value="images">Images (visual)</option>
                                                </select>
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - Watermark */}
                                    {tool === 'watermark' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">Add Watermark</h3>
                                            <div className="space-y-3">
                                                <div>
                                                    <label className="text-white text-sm font-medium">Type:</label>
                                                    <select
                                                        value={params.watermark_type || 'text'}
                                                        onChange={(e) => setParams({ ...params, watermark_type: e.target.value })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                    >
                                                        <option value="text">Text</option>
                                                        <option value="image">Image</option>
                                                    </select>
                                                </div>
                                                {(!params.watermark_type || params.watermark_type === 'text') && (
                                                    <>
                                                        <div>
                                                            <label className="text-white text-sm font-medium">Text:</label>
                                                            <input
                                                                type="text"
                                                                placeholder="WATERMARK"
                                                                onChange={(e) => setParams({ ...params, text: e.target.value })}
                                                                className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="text-white text-sm font-medium">Font Size:</label>
                                                            <input
                                                                type="number"
                                                                placeholder="60"
                                                                value={params.font_size || 60}
                                                                onChange={(e) => setParams({ ...params, font_size: parseInt(e.target.value) })}
                                                                className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                            />
                                                        </div>
                                                    </>
                                                )}
                                                <div>
                                                    <label className="text-white text-sm font-medium">Position:</label>
                                                    <select
                                                        value={params.position || 'center'}
                                                        onChange={(e) => setParams({ ...params, position: e.target.value })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                    >
                                                        <option value="center">Center</option>
                                                        <option value="topleft">Top Left</option>
                                                        <option value="topright">Top Right</option>
                                                        <option value="bottomleft">Bottom Left</option>
                                                        <option value="bottomright">Bottom Right</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - Page Numbers */}
                                    {tool === 'page_numbers' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">Add Page Numbers</h3>
                                            <div className="space-y-3">
                                                <div>
                                                    <label className="text-white text-sm font-medium">Position:</label>
                                                    <select
                                                        value={params.position || 'bottomright'}
                                                        onChange={(e) => setParams({ ...params, position: e.target.value })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                    >
                                                        <option value="bottom">Center Bottom</option>
                                                        <option value="bottomright">Bottom Right</option>
                                                        <option value="bottomleft">Bottom Left</option>
                                                        <option value="top">Center Top</option>
                                                        <option value="topright">Top Right</option>
                                                        <option value="topleft">Top Left</option>
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="text-white text-sm font-medium">Format:</label>
                                                    <input
                                                        type="text"
                                                        placeholder="{number}"
                                                        onChange={(e) => setParams({ ...params, format: e.target.value })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                    />
                                                    <p className="text-xs text-gray-400 mt-1">Use {'{number}'} and {'{total}'}</p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - Rotate */}
                                    {tool === 'rotate' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">Rotate Pages</h3>
                                            <div className="space-y-3">
                                                <div>
                                                    <label className="text-white text-sm font-medium">Angle:</label>
                                                    <select
                                                        value={params.angle || 90}
                                                        onChange={(e) => setParams({ ...params, angle: parseInt(e.target.value) })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none"
                                                    >
                                                        <option value={90}>90°</option>
                                                        <option value={180}>180°</option>
                                                        <option value={270}>270°</option>
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="text-white text-sm font-medium">Pages:</label>
                                                    <input
                                                        type="text"
                                                        placeholder="all"
                                                        onChange={(e) => setParams({ ...params, pages: e.target.value })}
                                                        className="w-full mt-1 bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                    />
                                                    <p className="text-xs text-gray-400 mt-1">e.g., 'all', '1,2,3', or '1-5'</p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - Metadata */}
                                    {tool === 'metadata' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">Edit Metadata</h3>
                                            <div className="space-y-3">
                                                <input
                                                    type="text"
                                                    placeholder="Title"
                                                    onChange={(e) => setParams({ ...params, title: e.target.value })}
                                                    className="w-full bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                />
                                                <input
                                                    type="text"
                                                    placeholder="Author"
                                                    onChange={(e) => setParams({ ...params, author: e.target.value })}
                                                    className="w-full bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                />
                                                <input
                                                    type="text"
                                                    placeholder="Subject"
                                                    onChange={(e) => setParams({ ...params, subject: e.target.value })}
                                                    className="w-full bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - Protect */}
                                    {tool === 'protect' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">Protect PDF</h3>
                                            <div className="space-y-3">
                                                <input
                                                    type="password"
                                                    placeholder="User Password"
                                                    onChange={(e) => setParams({ ...params, password: e.target.value })}
                                                    className="w-full bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                />
                                                <input
                                                    type="password"
                                                    placeholder="Owner Password (optional)"
                                                    onChange={(e) => setParams({ ...params, owner_password: e.target.value })}
                                                    className="w-full bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {/* Tool Options - Unlock */}
                                    {tool === 'unlock' && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-xl mb-4">Unlock PDF</h3>
                                            <input
                                                type="password"
                                                placeholder="PDF Password"
                                                onChange={(e) => setParams({ ...params, password: e.target.value })}
                                                className="w-full bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20 focus:border-violet-500 outline-none text-sm"
                                            />
                                        </div>
                                    )}

                                    {/* Tool Options - Compress (Resize UI) */}
                                    {tool === 'compress' && !downloadUrl && (
                                        <div className="mb-8 w-full text-center">
                                            <h3 className="text-white font-bold text-2xl mb-6">Compress / Resize PDF</h3>

                                            {/* Mode Selector */}
                                            <div className="flex justify-center gap-4 mb-6">
                                                <button
                                                    onClick={() => setParams({ ...params, mode: 'reduce', level: 'medium' })}
                                                    className={`px-6 py-2 rounded-full font-bold transition-all ${!params.mode || params.mode === 'reduce'
                                                        ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/30'
                                                        : 'bg-white/10 text-gray-400 hover:bg-white/20'
                                                        }`}
                                                >
                                                    Reduce Size
                                                </button>
                                                <button
                                                    onClick={() => setParams({ ...params, mode: 'increase' })}
                                                    className={`px-6 py-2 rounded-full font-bold transition-all ${params.mode === 'increase'
                                                        ? 'bg-pink-600 text-white shadow-lg shadow-pink-500/30'
                                                        : 'bg-white/10 text-gray-400 hover:bg-white/20'
                                                        }`}
                                                >
                                                    Increase Size
                                                </button>
                                            </div>

                                            {/* Target Input */}
                                            <div className="flex items-center justify-center gap-3 mb-2">
                                                <span className="text-white font-medium">Target Size (KB):</span>
                                                <input
                                                    type="number"
                                                    placeholder="100"
                                                    className="w-24 bg-white text-slate-900 font-bold text-center px-2 py-2 rounded-md outline-none focus:ring-2 focus:ring-violet-500"
                                                    onChange={(e) => setParams({ ...params, target_kb: e.target.value })}
                                                />
                                            </div>
                                            <p className="text-gray-500 text-xs">
                                                {params.mode === 'increase'
                                                    ? 'We will add safe metadata to reach this size.'
                                                    : 'We will attempt to compress to this size.'}
                                            </p>
                                        </div>
                                    )}

                                    {/* Upload Box */}
                                    {!downloadUrl && (
                                        <div className="relative group w-full">
                                            <input
                                                type="file"
                                                multiple
                                                onChange={(e) => setFiles(e.target.files)}
                                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                                                disabled={loading}
                                            />
                                            <div className="border-2 border-dashed border-violet-500/30 rounded-3xl p-12 text-center transition-all duration-300 bg-violet-500/5 group-hover:bg-violet-500/10 group-hover:border-violet-500/60">
                                                <div className="w-16 h-16 bg-violet-600 rounded-lg flex items-center justify-center mx-auto mb-4 shadow-lg shadow-violet-600/30">
                                                    <CloudArrowUpIcon className="w-8 h-8 text-white" />
                                                </div>
                                                <button className="bg-teal-700 hover:bg-teal-600 text-white font-bold py-2 px-6 rounded-lg transition-colors shadow-lg">
                                                    Select PDF
                                                </button>
                                                <p className="text-sm text-gray-500 mt-4">
                                                    or Drag & Drop PDF's Here
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Status / Error Messages */}
                                    {error && (
                                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 flex items-center gap-3">
                                            <XCircleIcon className="w-5 h-5 text-red-500" />
                                            {error}
                                        </div>
                                    )}

                                    {/* Action Button for Compress specific */}
                                    {tool === 'compress' && !downloadUrl && files && (
                                        <div className="w-full mt-4">
                                            <button
                                                onClick={handleUpload}
                                                disabled={loading}
                                                className="w-full py-4 rounded-xl font-bold text-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-xl transition-all"
                                            >
                                                {loading ? 'Compressing...' : 'Compress PDF'}
                                            </button>
                                        </div>
                                    )}

                                    {/* Standard Action Button for others */}
                                    {tool !== 'compress' && !downloadUrl && (
                                        <button
                                            onClick={handleUpload}
                                            disabled={loading || !files}
                                            className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-300 shadow-xl flex items-center justify-center gap-3 mt-6 ${loading || !files
                                                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                                : 'bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 text-white hover:shadow-fuchsia-500/30 hover:-translate-y-1'
                                                }`}
                                        >
                                            {loading ? (
                                                <>
                                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                    Processing...
                                                </>
                                            ) : (
                                                <>Start {activeTool.name}</>
                                            )}
                                        </button>
                                    )}

                                    {/* BATCH RESULT SCREEN */}
                                    {isBatch && batchJobs.length > 0 && (
                                        <div className="w-full space-y-4">
                                            <h3 className="text-white font-bold text-xl mb-4">Batch Results</h3>
                                            <div className="max-h-96 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                                                {batchJobs.map((job, idx) => (
                                                    <div key={idx} className="bg-white/10 rounded-xl p-4 flex items-center justify-between">
                                                        <div className="flex items-center gap-3 overflow-hidden">
                                                            <div className="p-2 bg-white/10 rounded-lg">
                                                                <activeTool.icon className="w-5 h-5 text-gray-300" />
                                                            </div>
                                                            <span className="text-white text-sm truncate max-w-[150px]">{job.filename || `File ${idx + 1}`}</span>
                                                        </div>

                                                        <div className="flex items-center gap-3">
                                                            {job.status === 'completed' ? (
                                                                <a
                                                                    href={job.downloadUrl}
                                                                    target="_blank"
                                                                    className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-xs font-bold rounded-lg flex items-center gap-2"
                                                                >
                                                                    <ArrowDownTrayIcon className="w-3 h-3" /> Download
                                                                </a>
                                                            ) : job.status === 'failed' ? (
                                                                <span className="text-red-400 text-xs font-bold px-3 py-2 bg-red-400/10 rounded-lg">Failed</span>
                                                            ) : (
                                                                <span className="text-yellow-400 text-xs font-bold px-3 py-2 bg-yellow-400/10 rounded-lg animate-pulse">
                                                                    {job.status || 'Queued'}...
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            <button
                                                onClick={() => { setBatchJobs([]); setIsBatch(false); setFiles(null); }}
                                                className="w-full py-3 bg-white/5 hover:bg-white/10 text-gray-400 text-sm font-bold rounded-xl mt-4"
                                            >
                                                Process New Batch
                                            </button>
                                        </div>
                                    )}

                                    {/* STATUS / SUCCESS SCREEN (Single) */}
                                    {!isBatch && downloadUrl && (
                                        <div className="w-full text-center animate-fade-in">
                                            {tool === 'compress' ? (
                                                /* Customized Compress Success UI */
                                                <div className="bg-white rounded-xl p-8 shadow-2xl">
                                                    <h3 className="text-2xl font-bold text-slate-800 mb-6">PDFs have been compressed!</h3>

                                                    <a
                                                        href={downloadUrl}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="block w-full py-4 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg text-lg shadow-lg mb-8 flex items-center justify-center gap-2"
                                                    >
                                                        <ArrowDownTrayIcon className="w-6 h-6" />
                                                        Download compressed PDF
                                                    </a>

                                                    {/* Stats Circle */}
                                                    <div className="flex items-center justify-center gap-6">
                                                        <div className="relative w-24 h-24 flex items-center justify-center">
                                                            {/* Simple CSS circle for demo */}
                                                            <div className="absolute inset-0 rounded-full border-4 border-slate-100"></div>
                                                            <div className={`absolute inset-0 rounded-full border-4 ${jobStats.compressed_size > jobStats.original_size ? 'border-pink-500' : 'border-red-500'
                                                                } border-t-transparent -rotate-45`}></div>
                                                            <div className="text-center z-10">
                                                                <div className="text-xl font-bold text-slate-800">
                                                                    {jobStats.saved_percent ? `${Math.abs(jobStats.saved_percent)}%` : 'Done'}
                                                                </div>
                                                                <div className="text-[10px] text-slate-500 font-bold uppercase">
                                                                    {jobStats.compressed_size > jobStats.original_size ? 'Increased' : 'Saved'}
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="text-left">
                                                            <p className="text-slate-600 font-medium">
                                                                {jobStats.compressed_size > jobStats.original_size
                                                                    ? 'Your PDF is now larger!'
                                                                    : 'Your PDF is now smaller!'}
                                                            </p>
                                                            <p className="text-slate-800 font-bold">
                                                                {jobStats.original_size ? (jobStats.original_size / 1024).toFixed(2) : '0'} KB
                                                                <span className="text-slate-400 mx-2">→</span>
                                                                {jobStats.compressed_size ? (jobStats.compressed_size / 1024).toFixed(2) : '0'} KB
                                                            </p>
                                                        </div>
                                                    </div>

                                                    <button
                                                        onClick={() => setDownloadUrl("")}
                                                        className="mt-8 text-slate-400 hover:text-slate-600 text-sm font-medium underline"
                                                    >
                                                        Process another file
                                                    </button>
                                                </div>
                                            ) : (
                                                /* Standard Success UI */
                                                <div>
                                                    <div className="mb-6">
                                                        <CheckCircleIcon className="w-20 h-20 text-green-500 mx-auto mb-4" />
                                                        <h3 className="text-2xl font-bold text-white mb-2">Ready for Download!</h3>
                                                        <p className="text-gray-400">Your files have been processed successfully.</p>
                                                    </div>
                                                    <a
                                                        href={downloadUrl}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="inline-flex items-center gap-2 py-4 px-8 rounded-xl font-bold text-lg bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-500/20 hover:shadow-green-500/40 hover:-translate-y-1 transition-all duration-300"
                                                    >
                                                        <ArrowDownTrayIcon className="w-6 h-6" />
                                                        Download File
                                                    </a>
                                                    <button
                                                        onClick={() => setDownloadUrl("")}
                                                        className="block w-full mt-4 text-gray-500 hover:text-white text-sm"
                                                    >
                                                        Process another file
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                </div>
                            </div>
                        </div>
                    </div>

                </main>

                {/* Footer */}
                <footer className="w-full py-8 text-center text-gray-600 text-sm">
                    &copy; {new Date().getFullYear()} PDFsimple. All rights reserved. Locally Secured.
                </footer>
            </div>
        </div>
    );
}
