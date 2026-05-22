"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { KitViewer } from "@/components/kit-viewer";
import toast from "react-hot-toast";

interface KitData {
  id: string;
  title: string;
  role_type: string;
  status: string;
  match_analysis: any;
  questions: any[];
  practical_test: any;
  rubric: any;
  red_flags: any[];
  flow_guide: any[];
}

export default function KitDetailPage() {
  const params = useParams();
  const kitId = params.id as string;
  const [kit, setKit] = useState<KitData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKit = async () => {
      try {
        const res = await apiClient.get(`/kits/${kitId}`);
        setKit(res.data);
      } catch {
        toast.error("Failed to load kit");
      } finally {
        setLoading(false);
      }
    };
    fetchKit();
  }, [kitId]);

  const handleExportPDF = async () => {
    try {
      const res = await apiClient.post(`/export/pdf/${kitId}`);
      window.open(res.data.pdf_url, "_blank");
      toast.success("PDF generated!");
    } catch {
      toast.error("PDF export failed");
    }
  };

  if (loading) return <div className="p-12 text-center text-gray-500">Loading kit...</div>;
  if (!kit) return <div className="p-12 text-center text-red-500">Kit not found</div>;

  return (
    <main className="max-w-5xl mx-auto py-12 px-4">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{kit.title}</h1>
          <p className="text-sm text-gray-500 mt-1">{kit.role_type.replace("_", " ")} • {kit.status}</p>
        </div>
        <button
          onClick={handleExportPDF}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
        >
          Export PDF
        </button>
      </div>

      <KitViewer kit={kit} />
    </main>
  );
}
