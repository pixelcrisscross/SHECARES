import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

const Report = () => {
  const { toast } = useToast();
  const [isAnonymous, setIsAnonymous] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast({ 
      title: "Report Submitted", 
      description: "Thank you for your courage. Your report has been submitted securely."
    });
  };

  return (
    <div className="min-h-screen bg-gradient-subtle flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Report an Incident</CardTitle>
          <CardDescription>Your voice matters. All reports are treated with confidentiality.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="incident-type">Type of Incident</Label>
              <Input id="incident-type" placeholder="e.g., Harassment, Unsafe Environment" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="date">Date of Incident</Label>
                <Input id="date" type="date" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="time">Time of Incident</Label>
                <Input id="time" type="time" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input id="location" placeholder="e.g., Street, City, or Online Platform" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" placeholder="Describe the incident in detail..." rows={5} />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="anonymous" checked={isAnonymous} onCheckedChange={(checked) => setIsAnonymous(checked as boolean)} />
              <Label htmlFor="anonymous">Submit Anonymously</Label>
            </div>
            {!isAnonymous && (
              <div className="space-y-4 pt-2 border-t">
                 <p className="text-sm text-muted-foreground">Optional: Provide your contact information if you are willing to be contacted for follow-up.</p>
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" placeholder="Your Name" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" placeholder="your@email.com" />
                </div>
              </div>
            )}
            <Button type="submit" className="w-full bg-gradient-primary">Submit Report</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Report;