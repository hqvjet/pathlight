"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, Clock, Zap, FileText } from "lucide-react";

export type GenerationItem = {
  course_id: string;
  user_id?: string;
  progress?: string;
  title_ready?: boolean;
  lessons_ready?: boolean;
  final_ready?: boolean;
  vectorized?: boolean;
  updated_at?: string;
};

function getGenerationStatus(item: GenerationItem) {
  const steps = [
    { key: 'vectorized', label: 'Docs', done: item.vectorized },
    { key: 'title_ready', label: 'Plan', done: item.title_ready },
    { key: 'lessons_ready', label: 'Lessons', done: item.lessons_ready },
    { key: 'final_ready', label: 'Test', done: item.final_ready },
  ];
  
  const completedSteps = steps.filter(s => s.done).length;
  const isComplete = completedSteps === steps.length;
  const currentStep = steps.find(s => !s.done);
  const progressPercent = (completedSteps / steps.length) * 100;
  
  return { steps, completedSteps, isComplete, currentStep, progressPercent };
}

// Truncate course ID for display
function getDisplayName(courseId: string) {
  if (courseId.length <= 20) return courseId;
  return courseId.slice(0, 17) + "...";
}

export default function GenerationCard({ 
  item, 
  onClick 
}: { 
  item: GenerationItem; 
  onClick?: () => void;
}) {
  const status = getGenerationStatus(item);
  const updated = item.updated_at ? new Date(item.updated_at).toLocaleDateString('vi-VN') : "";
  const displayName = getDisplayName(item.course_id);

  return (
    <Card 
      className="group p-5 hover:shadow-lg transition-all duration-300 border-gray-100 cursor-pointer hover:border-orange-200 bg-white"
      onClick={onClick}
    >
      <div className="space-y-5">
        {/* Header - More spacious */}
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-400 via-pink-400 to-purple-500 text-white flex items-center justify-center font-bold text-lg shadow-md shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 
              className="font-semibold text-gray-900 group-hover:text-orange-600 transition-colors text-base leading-tight mb-1" 
              title={item.course_id}
            >
              {displayName}
            </h3>
            <p className="text-xs text-gray-500">{updated}</p>
          </div>
          {status.isComplete ? (
            <Badge className="bg-emerald-500 text-white shadow-sm shrink-0">
              <CheckCircle className="w-3 h-3 mr-1" />
              Done
            </Badge>
          ) : (
            <Badge variant="outline" className="border-orange-200 text-orange-600 shrink-0">
              <Clock className="w-3 h-3 mr-1" />
              Processing
            </Badge>
          )}
        </div>

        {/* Progress - Clean and simple */}
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Progress</span>
            <span className="font-medium text-gray-900">{status.completedSteps}/{status.steps.length} steps</span>
          </div>
          <Progress value={status.progressPercent} className="h-2" />
        </div>

        {/* Current Status - Only show if in progress */}
        {!status.isComplete && status.currentStep && (
          <div className="flex items-center gap-2 p-3 bg-orange-50 rounded-lg border border-orange-100">
            <Zap className="w-4 h-4 text-orange-500" />
            <span className="text-sm text-orange-700">
              Working on: <strong>{status.currentStep.label}</strong>
            </span>
          </div>
        )}

        {/* Simple step indicators - horizontal layout */}
        <div className="flex justify-between">
          {status.steps.map((step) => (
            <div key={step.key} className="flex flex-col items-center gap-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                step.done 
                  ? 'bg-emerald-500 text-white' 
                  : 'bg-gray-200 text-gray-500'
              }`}>
                {step.done ? <CheckCircle className="w-4 h-4" /> : step.key.charAt(0).toUpperCase()}
              </div>
              <span className="text-xs text-gray-600">{step.label}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
