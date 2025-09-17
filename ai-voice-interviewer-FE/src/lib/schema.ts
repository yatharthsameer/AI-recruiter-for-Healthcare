import { z } from "zod";

// Application form schema
export const applicationSchema = z.object({
  // Contact details (mandatory)
  firstName: z.string().min(2, "First name must be at least 2 characters").max(40, "First name must be less than 40 characters"),
  lastName: z.string().min(2, "Last name must be at least 2 characters").max(40, "Last name must be less than 40 characters"),
  email: z.string().email("Please enter a valid email address"),
  phone: z.string().min(7, "Please enter a valid phone number").max(15, "Phone number is too long"),
  
  // Caregiving experience (mandatory)
  caregivingExperience: z.boolean({
    required_error: "Please select an option",
  }),
  
  // PER ID questions
  hasPerId: z.boolean({
    required_error: "Please select an option",
  }),
  perId: z.string().transform(val => val === "" ? undefined : val).optional(), // Optional field
  
  // SSN (optional)
  ssn: z.string().transform(val => val === "" ? undefined : val).optional(), // Optional field
  
  // License and insurance (mandatory)
  driversLicense: z.boolean({
    required_error: "Please select an option",
  }),
  autoInsurance: z.boolean({
    required_error: "Please select an option",
  }),
  
  // Availability (mandatory)
  availability: z.array(
    z.enum(["Morning", "Afternoon", "Evening", "Overnight", "Weekend"])
  ).min(1, "Please select at least one availability option"),
  
  // Weekly hours (mandatory)
  weeklyHours: z.number().int().min(5, "Minimum 5 hours per week").max(80, "Maximum 80 hours per week"),
  
  // Languages (optional for now, can be moved to interview later)
  languages: z.array(z.string()).optional(),
});

export type ApplicationData = z.infer<typeof applicationSchema>;

// Device setup schema
export const deviceSetupSchema = z.object({
  cameraId: z.string().optional(),
  microphoneId: z.string().optional(),
  speakerId: z.string().optional(),
  hasVideoStream: z.boolean(),
  hasAudioStream: z.boolean(),
});

export type DeviceSetupData = z.infer<typeof deviceSetupSchema>;

// Combined form data
export const interviewDataSchema = z.object({
  application: applicationSchema,
  deviceSetup: deviceSetupSchema,
});

export type InterviewData = z.infer<typeof interviewDataSchema>;