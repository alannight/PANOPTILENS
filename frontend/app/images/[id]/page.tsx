"use client";

import { useParams } from "next/navigation";
import { ImageAnalysisView } from "@/features/images/image-analysis-view";

export default function ImageDetailsPage() {
  const params = useParams();
  const imageId = params.id as string;

  return <ImageAnalysisView imageId={imageId} />;
}
