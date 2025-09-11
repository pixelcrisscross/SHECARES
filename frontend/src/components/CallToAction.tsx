import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const CallToAction = () => {
  return (
    <section className="py-20 bg-gradient-soft">
      <div className="container mx-auto px-4 text-center">
        <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
          <h2 className="text-4xl md:text-5xl font-bold">
            Ready to Take Control of
            <span className="bg-gradient-primary bg-clip-text text-transparent"> Your Health?</span>
          </h2>
          <p className="text-xl text-muted-foreground leading-relaxed">
            Join thousands of women who trust WellnessHer for their complete health journey. 
            Start tracking, get support, and stay safe with our comprehensive platform.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              size="lg" 
              className="bg-gradient-primary hover:opacity-90 shadow-glow text-lg px-12 py-6"
              asChild
            >
              <Link to="/auth">Get Started Today</Link>
            </Button>
          </div>
          
          <div className="flex flex-wrap justify-center gap-8 pt-8 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Free to start</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>No credit card required</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Privacy protected</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>24/7 emergency support</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CallToAction;