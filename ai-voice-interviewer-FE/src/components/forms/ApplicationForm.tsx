import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import PhoneInput from "react-phone-number-input/input";
import 'react-phone-number-input/style.css';

import { applicationSchema, ApplicationData } from "@/lib/schema";
import { useInterview, interviewActions } from "@/lib/store.tsx";
import { useToast } from "@/hooks/use-toast";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";

export default function ApplicationForm() {
  const { state, dispatch } = useInterview();
  const navigate = useNavigate();
  const { toast } = useToast();

  const form = useForm<ApplicationData>({
    resolver: zodResolver(applicationSchema),
    mode: "onChange", // Validate on every change
    defaultValues: {
      firstName: state.application?.firstName || "",
      lastName: state.application?.lastName || "",
      email: state.application?.email || "",
      phone: state.application?.phone || "",
      caregivingExperience: state.application?.caregivingExperience || undefined,
      hasPerId: state.application?.hasPerId || undefined,
      perId: state.application?.perId || "",
      ssn: state.application?.ssn || "",
      driversLicense: state.application?.driversLicense || undefined,
      autoInsurance: state.application?.autoInsurance || undefined,
      availability: state.application?.availability || [],
      weeklyHours: state.application?.weeklyHours || 30,
      languages: state.application?.languages || [],
    },
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting, isValid },
  } = form;

  const watchedData = watch();

  // Auto-save to store on form changes
  React.useEffect(() => {
    dispatch(interviewActions.updateApplication(watchedData));
  }, [watchedData, dispatch]);

  const onSubmit = async (data: ApplicationData) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      dispatch(interviewActions.updateApplication(data));
      dispatch(interviewActions.markApplicationComplete(true));
      dispatch(interviewActions.setStep(2));
      
      toast({
        title: "Application saved!",
        description: "Your application has been successfully submitted.",
      });
      
      navigate("/interview");
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save application. Please try again.",
        variant: "destructive",
      });
    }
  };

  const availabilityOptions = ["Morning", "Afternoon", "Evening", "Overnight", "Weekend"];
  const languageOptions = ["English", "Spanish", "Mandarin", "Others"];

  // Check if all mandatory fields are filled (excluding optional fields like perId and ssn)
  const isMandatoryFieldsFilled = () => {
    return (
      watchedData.firstName &&
      watchedData.firstName.length >= 2 &&
      watchedData.lastName &&
      watchedData.lastName.length >= 2 &&
      watchedData.email &&
      watchedData.email.includes('@') &&
      watchedData.phone &&
      watchedData.phone.length >= 7 &&
      watchedData.caregivingExperience !== undefined &&
      watchedData.hasPerId !== undefined &&
      watchedData.driversLicense !== undefined &&
      watchedData.autoInsurance !== undefined &&
      watchedData.availability &&
      watchedData.availability.length > 0 &&
      watchedData.weeklyHours &&
      watchedData.weeklyHours >= 5
      // Note: perId and ssn are optional, so we don't check them here
      // Note: languages are optional, so we don't check them here
    );
  };

  // Use Zod validation as primary validation, custom check as backup
  const isFormValid = isValid || isMandatoryFieldsFilled();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="form-container"
    >
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Tell us about you</h1>
        <p className="text-muted-foreground">A few quick details to match you with roles.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Contact Details */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Contact Details</h2>
          
          {/* Name Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name *</Label>
              <Input
                id="firstName"
                {...register("firstName")}
                autoComplete="given-name"
                className={errors.firstName ? "border-destructive" : ""}
              />
              {errors.firstName && (
                <p className="text-sm text-destructive">{errors.firstName.message}</p>
              )}
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name *</Label>
              <Input
                id="lastName"
                {...register("lastName")}
                autoComplete="family-name"
                className={errors.lastName ? "border-destructive" : ""}
              />
              {errors.lastName && (
                <p className="text-sm text-destructive">{errors.lastName.message}</p>
              )}
            </div>
          </div>

          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              {...register("email")}
              autoComplete="email"
              className={errors.email ? "border-destructive" : ""}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          {/* Phone */}
          <div className="space-y-2">
            <Label htmlFor="phone">Phone *</Label>
            <PhoneInput
              id="phone"
              country="US"
              value={watchedData.phone}
              onChange={(value) => setValue("phone", value || "")}
              className={`PhoneInputInput ${errors.phone ? "border-destructive" : ""}`}
              inputMode="tel"
              autoComplete="tel"
            />
            {errors.phone && (
              <p className="text-sm text-destructive">{errors.phone.message}</p>
            )}
          </div>
        </div>

        {/* Caregiving Experience */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Experience</h2>
          
          <div className="space-y-3">
            <Label>Do you have caregiving experience (working as a home care professional)? *</Label>
            <RadioGroup
              value={watchedData.caregivingExperience?.toString()}
              onValueChange={(value) => setValue("caregivingExperience", value === "true")}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id="caregiving-yes" />
                <Label htmlFor="caregiving-yes" className="font-normal cursor-pointer">Yes</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id="caregiving-no" />
                <Label htmlFor="caregiving-no" className="font-normal cursor-pointer">No</Label>
              </div>
            </RadioGroup>
            {errors.caregivingExperience && (
              <p className="text-sm text-destructive">{errors.caregivingExperience.message}</p>
            )}
          </div>
        </div>

        {/* PER ID Section */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Certification</h2>
          
          <div className="space-y-3">
            <Label>Do you have a PER ID? *</Label>
            <RadioGroup
              value={watchedData.hasPerId?.toString()}
              onValueChange={(value) => setValue("hasPerId", value === "true")}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id="per-yes" />
                <Label htmlFor="per-yes" className="font-normal cursor-pointer">Yes</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id="per-no" />
                <Label htmlFor="per-no" className="font-normal cursor-pointer">No</Label>
              </div>
            </RadioGroup>
            {errors.hasPerId && (
              <p className="text-sm text-destructive">{errors.hasPerId.message}</p>
            )}
          </div>

          {/* PER ID Input - Optional */}
          <div className="space-y-2">
            <Label htmlFor="perId">Please share your PER ID (optional)</Label>
            <Input
              id="perId"
              {...register("perId")}
              placeholder="Enter your PER ID"
              className={errors.perId ? "border-destructive" : ""}
            />
            {errors.perId && (
              <p className="text-sm text-destructive">{errors.perId.message}</p>
            )}
          </div>

          {/* SSN - Optional */}
          <div className="space-y-2">
            <Label htmlFor="ssn">Share your SSN (optional)</Label>
            <Input
              id="ssn"
              type="password"
              {...register("ssn")}
              placeholder="Enter your SSN"
              className={errors.ssn ? "border-destructive" : ""}
            />
            {errors.ssn && (
              <p className="text-sm text-destructive">{errors.ssn.message}</p>
            )}
            <p className="text-xs text-muted-foreground">This information is kept secure and confidential</p>
          </div>
        </div>

        {/* License and Insurance */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">License & Insurance</h2>
          
          <div className="space-y-3">
            <Label>Do you have a driving license? *</Label>
            <RadioGroup
              value={watchedData.driversLicense?.toString()}
              onValueChange={(value) => setValue("driversLicense", value === "true")}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id="license-yes" />
                <Label htmlFor="license-yes" className="font-normal cursor-pointer">Yes</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id="license-no" />
                <Label htmlFor="license-no" className="font-normal cursor-pointer">No</Label>
              </div>
            </RadioGroup>
            {errors.driversLicense && (
              <p className="text-sm text-destructive">{errors.driversLicense.message}</p>
            )}
          </div>

          <div className="space-y-3">
            <Label>Do you have auto insurance? *</Label>
            <RadioGroup
              value={watchedData.autoInsurance?.toString()}
              onValueChange={(value) => setValue("autoInsurance", value === "true")}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id="insurance-yes" />
                <Label htmlFor="insurance-yes" className="font-normal cursor-pointer">Yes</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id="insurance-no" />
                <Label htmlFor="insurance-no" className="font-normal cursor-pointer">No</Label>
              </div>
            </RadioGroup>
            {errors.autoInsurance && (
              <p className="text-sm text-destructive">{errors.autoInsurance.message}</p>
            )}
          </div>
        </div>

        {/* Availability */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Availability</h2>
          
          <div className="space-y-3">
            <Label>What are your available hours to work? *</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {availabilityOptions.map((option) => (
                <div key={option} className="flex items-center space-x-2">
                  <Checkbox
                    id={`availability-${option}`}
                    checked={watchedData.availability?.includes(option as any)}
                    onCheckedChange={(checked) => {
                      const current = watchedData.availability || [];
                      if (checked) {
                        setValue("availability", [...current, option as any]);
                      } else {
                        setValue("availability", current.filter(item => item !== option));
                      }
                    }}
                  />
                  <Label htmlFor={`availability-${option}`} className="font-normal cursor-pointer">
                    {option}
                  </Label>
                </div>
              ))}
            </div>
            {errors.availability && (
              <p className="text-sm text-destructive">{errors.availability.message}</p>
            )}
          </div>

          {/* Weekly Hours */}
          <div className="space-y-4">
            <Label>How many hours would you like to work a week? *</Label>
            <div className="space-y-4">
              <Slider
                value={[watchedData.weeklyHours]}
                onValueChange={([value]) => setValue("weeklyHours", value)}
                max={80}
                min={5}
                step={1}
                className="w-full"
              />
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>5 hours</span>
                <div className="flex items-center space-x-2">
                  <Input
                    type="number"
                    min={5}
                    max={80}
                    value={watchedData.weeklyHours}
                    onChange={(e) => setValue("weeklyHours", parseInt(e.target.value) || 5)}
                    className="w-20 text-center"
                  />
                  <span>hours/week</span>
                </div>
                <span>80 hours</span>
              </div>
            </div>
            {errors.weeklyHours && (
              <p className="text-sm text-destructive">{errors.weeklyHours.message}</p>
            )}
          </div>
        </div>

        {/* Languages - Optional */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Languages (Optional)</h2>
          
          <div className="space-y-3">
            <Label>Languages spoken</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {languageOptions.map((language) => (
                <div key={language} className="flex items-center space-x-2">
                  <Checkbox
                    id={`language-${language}`}
                    checked={watchedData.languages?.includes(language)}
                    onCheckedChange={(checked) => {
                      const current = watchedData.languages || [];
                      if (checked) {
                        setValue("languages", [...current, language]);
                      } else {
                        setValue("languages", current.filter(item => item !== language));
                      }
                    }}
                  />
                  <Label htmlFor={`language-${language}`} className="font-normal cursor-pointer">
                    {language}
                  </Label>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Select all languages you can communicate in</p>
          </div>
        </div>

        {/* Privacy Notice */}
        <div className="bg-muted/50 p-4 rounded-lg">
          <p className="text-xs text-muted-foreground text-center">
            Your information is used only for hiring purposes and is never sold or shared with third parties.
          </p>
        </div>

        {/* Submit Button */}
        <div className="pt-4">
          <Button
            type="submit"
            disabled={!isFormValid || isSubmitting}
            className="w-full h-12 text-base font-semibold"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving Application...
              </>
            ) : (
              "Next: Interview Setup"
            )}
          </Button>
        </div>
      </form>
    </motion.div>
  );
}