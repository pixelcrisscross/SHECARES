import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Calendar, Baby, Heart, MessageCircle, Utensils, Loader2, CheckCircle, XCircle } from "lucide-react";
import { useNavigate } from 'react-router-dom';
import { useAuthState } from 'react-firebase-hooks/auth';
import { auth } from '@/config/firebase';
import EmergencySafety from "@/components/EmergencySafety";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

interface DueDateResult {
  estimated_due_date: string;
}

interface FoodAnalysisResult {
  items: string[];
  safe_to_eat: boolean;
  confidence_score: number;
  pros: string[];
  cons: string[];
}

const PregnancyCare = () => {
  const [user] = useAuthState(auth);
  const navigate = useNavigate();

  const [lmpDate, setLmpDate] = useState('');
  const [dueDate, setDueDate] = useState<DueDateResult | null>(null);
  const [dueDateLoading, setDueDateLoading] = useState(false);
  const [dueDateError, setDueDateError] = useState<string | null>(null);

  const [foodImage, setFoodImage] = useState<File | null>(null);
  const [foodAnalysis, setFoodAnalysis] = useState<FoodAnalysisResult | null>(null);
  const [foodLoading, setFoodLoading] = useState(false);
  const [foodError, setFoodError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!user) {
    navigate('/auth');
    return null;
  }

  const handleDueDateCalculate = async () => {
    if (!lmpDate) {
      setDueDateError('Please select a date.');
      return;
    }
    setDueDateLoading(true);
    setDueDateError(null);
    setDueDate(null);
    try {
      const response = await fetch('http://localhost:8000/calculate-due-date', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lmp_date: lmpDate })
      });
      if (!response.ok) throw new Error('Failed to calculate due date.');
      const result: DueDateResult = await response.json();
      setDueDate(result);
    } catch (err: any) {
      setDueDateError(err.message);
    } finally {
      setDueDateLoading(false);
    }
  };

  const handleFoodAnalyze = async () => {
    if (!foodImage) {
      setFoodError('Please select an image file.');
      return;
    }
    setFoodLoading(true);
    setFoodError(null);
    setFoodAnalysis(null);
    const formData = new FormData();
    formData.append('file', foodImage);
    try {
      const response = await fetch('http://localhost:8000/analyse-food', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to analyze food image.');
      const result: FoodAnalysisResult = await response.json();
      setFoodAnalysis(result);
    } catch (err: any) {
      setFoodError(err.message);
    } finally {
      setFoodLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Header />
      
      <main className="container mx-auto px-4 py-8 mt-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4">
              👶 <span className="bg-gradient-primary bg-clip-text text-transparent">Pregnancy Care</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Complete pregnancy tracking with personalized care and support
            </p>
          </div>

          <EmergencySafety />

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Calendar className="h-5 w-5" />Due Date Calculator</CardTitle>
                <CardDescription>Enter your last menstrual period to estimate your due date.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="lmp-date">Last Menstrual Period Date</Label>
                    <Input id="lmp-date" type="date" value={lmpDate} onChange={(e) => setLmpDate(e.target.value)} />
                  </div>
                  <Button onClick={handleDueDateCalculate} disabled={dueDateLoading} className="w-full">
                    {dueDateLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Calculate
                  </Button>
                  {dueDateError && <Alert variant="destructive"><AlertDescription>{dueDateError}</AlertDescription></Alert>}
                  {dueDate && (
                    <div className="bg-primary/10 p-4 rounded-lg text-center">
                      <p className="text-sm text-muted-foreground mb-1">Estimated Due Date</p>
                      <p className="text-lg font-semibold">{new Date(dueDate.estimated_due_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Utensils className="h-5 w-5" />Food Analyzer</CardTitle>
                <CardDescription>Upload an image to check if a food is safe for pregnancy.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                   <Input
                    id="food-image"
                    type="file"
                    accept="image/*"
                    ref={fileInputRef}
                    onChange={(e) => setFoodImage(e.target.files ? e.target.files[0] : null)}
                    className="hidden"
                  />
                  <Button onClick={() => fileInputRef.current?.click()} variant="outline" className="w-full">
                     {foodImage ? foodImage.name : 'Select Food Image'}
                  </Button>
                  <Button onClick={handleFoodAnalyze} disabled={foodLoading} className="w-full">
                    {foodLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Analyze Food
                  </Button>
                  {foodError && <Alert variant="destructive"><AlertDescription>{foodError}</AlertDescription></Alert>}
                   {foodAnalysis && (
                    <div className={foodAnalysis.safe_to_eat ? "border-green-500" : "border-red-500" + " border p-4 rounded-lg"}>
                      <div className="flex items-center gap-2 mb-2">
                        {foodAnalysis.safe_to_eat ? <CheckCircle className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-red-500" />}
                        <CardTitle>{foodAnalysis.safe_to_eat ? "Safe to Eat" : "Caution Advised"}</CardTitle>
                      </div>
                      <p className="text-sm text-muted-foreground font-semibold">Identified items: {foodAnalysis.items.join(', ')}</p>
                      <div className="mt-2">
                        <p className="text-sm font-semibold">Pros:</p>
                        <ul className="list-disc list-inside text-sm text-muted-foreground">{foodAnalysis.pros.map((pro, i) => <li key={i}>{pro}</li>)}</ul>
                      </div>
                      <div className="mt-2">
                        <p className="text-sm font-semibold">Cons:</p>
                        <ul className="list-disc list-inside text-sm text-muted-foreground">{foodAnalysis.cons.map((con, i) => <li key={i}>{con}</li>)}</ul>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default PregnancyCare;