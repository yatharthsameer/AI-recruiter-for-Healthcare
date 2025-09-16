"""
Simple API server to serve interview data to the admin panel
"""
import os
import glob
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import re
import wave

app = FastAPI(title="Interview Data API", version="1.0.0")

# Enable CORS for the admin panel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Relaxed for local development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Accept-Ranges", "Content-Range", "Content-Length"]
)

# Mount static files for interview outputs so FE can load audio
try:
    outputs_dir = os.path.join(os.getcwd(), "interview-outputs")
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir, exist_ok=True)
    app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")
except Exception as e:
    print(f"Failed to mount static outputs: {e}")

# Directory containing interview outputs
INTERVIEW_OUTPUTS_DIR = "interview-outputs"

class InterviewDataService:
    @staticmethod
    def _build_competency_segments(responses: List[Dict[str, Any]], full_audio: Optional[Dict[str, Any]]) -> Dict[str, List[Dict[str, int]]]:
        comp_map: Dict[str, List[Dict[str, int]]] = {}
        try:
            times = {}
            if full_audio and isinstance(full_audio.get('segments'), list):
                for seg in full_audio['segments']:
                    times[int(seg.get('questionNumber', 0))] = {
                        'startMs': int(seg.get('startMs', 0)),
                        'endMs': int(seg.get('endMs', 0)),
                    }
            for r in responses:
                qn = int(r.get('questionNumber', 0))
                if qn <= 0: continue
                si = (r.get('analysis', {}) or {}).get('scoreImpact', {})
                for comp, weight in (si.items() if isinstance(si, dict) else []):
                    if isinstance(weight, int) and weight != 0:  # Include both positive AND negative weights
                        t = times.get(qn, {'startMs': r.get('startMs', 0), 'endMs': r.get('endMs', 0)})
                        comp_map.setdefault(comp, []).append({
                            'questionNumber': qn,
                            'startMs': int(t.get('startMs', 0)),
                            'endMs': int(t.get('endMs', 0)),
                            'weight': abs(weight),  # Use absolute weight for UI highlighting, but keep track of negatives
                        })
                        
            # Add segments for competencies that should be evaluated but got 0 scores (concerning responses)
            # These are particularly important for safety and communication issues
            concerning_competencies = ['safety_awareness', 'communication_skills']
            for r in responses:
                qn = int(r.get('questionNumber', 0))
                if qn <= 0: continue
                si = (r.get('analysis', {}) or {}).get('scoreImpact', {})
                flags = (r.get('analysis', {}) or {}).get('flags', [])
                
                # Check if response has concerning content but zero scores
                has_concerning_flags = any(flag for flag in flags if 
                    'concern' in flag.lower() or 'unsafe' in flag.lower() or 
                    'ethical' in flag.lower() or 'communication' in flag.lower())
                
                # Check response content for specific issues
                response_text = r.get('response', '').lower()
                has_safety_issues = any(word in response_text for word in [
                    'hide', 'secret', 'covert', 'sneak', 'medication inside food',
                    'without telling', 'force', 'unsafe'
                ])
                has_communication_issues = any(phrase in response_text for phrase in [
                    'uh', 'um', 'like', 'basically', 'stuff', 'and stuff'
                ]) and response_text.count('uh') + response_text.count('um') > 2
                
                for comp in concerning_competencies:
                    should_highlight = False
                    weight = 1
                    
                    if comp == 'safety_awareness':
                        should_highlight = (comp in si and si[comp] == 0) or has_safety_issues or has_concerning_flags
                        weight = 3 if has_safety_issues else 1
                    elif comp == 'communication_skills':
                        should_highlight = (comp in si and si[comp] == 0) or has_communication_issues
                        weight = 2 if has_communication_issues else 1
                    
                    if should_highlight:
                        t = times.get(qn, {'startMs': r.get('startMs', 0), 'endMs': r.get('endMs', 0)})
                        # Only add if not already present
                        if comp not in comp_map or not any(seg['questionNumber'] == qn for seg in comp_map[comp]):
                            comp_map.setdefault(comp, []).append({
                                'questionNumber': qn,
                                'startMs': int(t.get('startMs', 0)),
                                'endMs': int(t.get('endMs', 0)),
                                'weight': weight,
                            })
                            
        except Exception as e:
            print(f"Error building competency segments: {e}")
            return {}
        return comp_map
    """Service to parse and serve interview data"""
    
    @staticmethod
    def get_all_interviews() -> List[Dict[str, Any]]:
        """Get all completed interviews"""
        interviews = []
        
        if not os.path.exists(INTERVIEW_OUTPUTS_DIR):
            return interviews
        
        # Find all evaluation files (JSON only)
        evaluation_files = glob.glob(os.path.join(INTERVIEW_OUTPUTS_DIR, "evaluation_*.json"))
        
        for eval_file in evaluation_files:
            try:
                # Extract session ID from filename
                session_id = InterviewDataService._extract_session_id(eval_file)
                if not session_id:
                    continue
                
                # Parse evaluation file (JSON only)
                evaluation_data = InterviewDataService._parse_evaluation_json(eval_file)
                
                # Find corresponding transcript file by session ID (JSON only)
                transcript_json_pattern = os.path.join(INTERVIEW_OUTPUTS_DIR, f"transcript_{session_id}_*.json")
                transcript_files_json = glob.glob(transcript_json_pattern)
                transcript_data = None
                if transcript_files_json:
                    transcript_data = InterviewDataService._parse_transcript_json(transcript_files_json[0], session_id)
                else:
                    print(f"No transcript JSON file found for session {session_id}")
                
                # Combine data
                interview = {
                    "sessionId": session_id,
                    "status": "completed",
                    "interviewType": evaluation_data.get("interviewType", "general"),
                    "userData": evaluation_data.get("userData", {}),
                    "startTime": evaluation_data.get("startTime"),
                    "endTime": evaluation_data.get("endTime"),
                    "duration": evaluation_data.get("duration", 0),
                    "caregiverEvaluation": evaluation_data.get("evaluation", {}),
                    "transcript": transcript_data,
                    "metadata": {
                        "lastActivity": evaluation_data.get("endTime"),
                        "clientIp": "127.0.0.1",  # Default for now
                        "userAgent": "Unknown"
                    }
                }
                
                interviews.append(interview)
                
            except Exception as e:
                print(f"Error processing {eval_file}: {e}")
                continue
        
        # Sort by date (newest first)
        interviews.sort(key=lambda x: x.get("startTime", ""), reverse=True)
        return interviews
    
    @staticmethod
    def get_interview_by_id(session_id: str) -> Optional[Dict[str, Any]]:
        """Get specific interview by session ID"""
        interviews = InterviewDataService.get_all_interviews()
        return next((i for i in interviews if i["sessionId"] == session_id), None)
    
    @staticmethod
    def _extract_session_id(filename: str) -> Optional[str]:
        """Extract session ID from filename"""
        match = re.search(r'evaluation_([a-f0-9\-]+)_', filename)
        return match.group(1) if match else None
    
    @staticmethod
    def _parse_evaluation_file(filepath: str) -> Dict[str, Any]:
        """Parse evaluation text file"""
        data = {
            "userData": {},
            "evaluation": {},
            "interviewType": "general",
            "duration": 0
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic info
            if "Candidate:" in content:
                name_match = re.search(r'Candidate:\s*(.+)', content)
                if name_match:
                    full_name = name_match.group(1).strip()
                    name_parts = full_name.split()
                    data["userData"]["firstName"] = name_parts[0] if name_parts else ""
                    data["userData"]["lastName"] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            if "Email:" in content:
                email_match = re.search(r'Email:\s*(.+)', content)
                if email_match:
                    data["userData"]["email"] = email_match.group(1).strip()
            
            if "Phone:" in content:
                phone_match = re.search(r'Phone:\s*(.+)', content)
                if phone_match:
                    data["userData"]["phone"] = phone_match.group(1).strip()
            
            if "Position Applied:" in content:
                position_match = re.search(r'Position Applied:\s*(.+)', content)
                if position_match:
                    data["userData"]["position"] = position_match.group(1).strip().lower()
            
            if "Interview Type:" in content:
                type_match = re.search(r'Interview Type:\s*(.+)', content)
                if type_match:
                    data["interviewType"] = type_match.group(1).strip().lower()
            
            # Extract overall score
            score_match = re.search(r'Overall Score:\s*(\d+)/100', content)
            if score_match:
                data["evaluation"]["overallScore"] = int(score_match.group(1))
            
            # Extract duration
            duration_match = re.search(r'Duration:\s*([\d.]+)\s*seconds', content)
            if duration_match:
                data["duration"] = float(duration_match.group(1))
            
            # Extract recommendation
            rec_match = re.search(r'\*\*Recommendation:\*\*\s*(.+)', content)
            if rec_match:
                data["evaluation"]["recommendation"] = {
                    "recommendation": rec_match.group(1).strip(),
                    "confidence": "Medium",  # Default
                    "reasoning": "Based on interview performance"
                }
            
            # Extract competency scores (simplified parsing)
            competency_scores = {}
            competency_patterns = {
                "empathy_compassion": r'\*\*Empathy & Compassion:\*\*\s*\[(\d+)/10\]',
                "safety_awareness": r'\*\*Safety Awareness:\*\*\s*\[(\d+)/10\]',
                "communication_skills": r'\*\*Communication Skills:\*\*\s*\[(\d+)/10\]',
                "problem_solving": r'\*\*Problem-Solving:\*\*\s*\[(\d+)/10\]',
                "experience_commitment": r'\*\*Experience & Commitment:\*\*\s*\[(\d+)/10\]'
            }
            
            for key, pattern in competency_patterns.items():
                match = re.search(pattern, content)
                if match:
                    competency_scores[key] = int(match.group(1))
                else:
                    competency_scores[key] = 5  # Default score
            
            data["evaluation"]["competencyScores"] = competency_scores
            
            # Extract strengths and development areas (simplified)
            strengths = []
            dev_areas = []
            
            # Look for bullet points after "KEY STRENGTHS" section
            strengths_section = re.search(r'\*\*3\) KEY STRENGTHS\*\*(.*?)\*\*4\)', content, re.DOTALL)
            if strengths_section:
                strength_matches = re.findall(r'\*\s*\*\*(.+?):\*\*', strengths_section.group(1))
                strengths = [s.strip() for s in strength_matches]
            
            # Look for development areas
            dev_section = re.search(r'\*\*4\) DEVELOPMENT AREAS\*\*(.*?)\*\*5\)', content, re.DOTALL)
            if dev_section:
                dev_matches = re.findall(r'\*\s*\*\*(.+?):\*\*', dev_section.group(1))
                dev_areas = [d.strip() for d in dev_matches]
            
            data["evaluation"]["strengths"] = strengths
            data["evaluation"]["developmentAreas"] = dev_areas
            
            # Extract next steps
            next_steps = []
            steps_section = re.search(r'\*\*7\) NEXT STEPS\*\*(.*?)(?:\*\*|$)', content, re.DOTALL)
            if steps_section:
                step_matches = re.findall(r'\*\s*\*\*(.+?):\*\*', steps_section.group(1))
                next_steps = [s.strip() for s in step_matches]
            
            data["evaluation"]["nextSteps"] = next_steps
            
            # Set timestamps (extract from filename or use current time)
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})', filepath)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1).replace('-', ':', 2).replace('-', ':')
                try:
                    dt = datetime.fromisoformat(timestamp_str)
                    data["startTime"] = dt.isoformat()
                    data["endTime"] = dt.isoformat()
                except Exception:
                    data["startTime"] = datetime.now().isoformat()
                    data["endTime"] = datetime.now().isoformat()
            else:
                data["startTime"] = datetime.now().isoformat()
                data["endTime"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Error parsing evaluation file {filepath}: {e}")
        
        return data

    @staticmethod
    def _parse_evaluation_json(filepath: str) -> Dict[str, Any]:
        """Parse evaluation JSON file"""
        data: Dict[str, Any] = {
            "userData": {},
            "evaluation": {},
            "interviewType": "general",
            "duration": 0
        }
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw = json.load(f)

            # Map common fields
            eval_block: Dict[str, Any] = {}
            if 'overallScore' in raw:
                eval_block['overallScore'] = raw['overallScore']
            if 'recommendation' in raw:
                eval_block['recommendation'] = raw['recommendation']
            if 'competencyScores' in raw:
                eval_block['competencyScores'] = raw['competencyScores']
            if 'strengths' in raw:
                eval_block['strengths'] = raw['strengths']
            if 'developmentAreas' in raw:
                eval_block['developmentAreas'] = raw['developmentAreas']
            if 'nextSteps' in raw:
                eval_block['nextSteps'] = raw['nextSteps']

            data['evaluation'] = eval_block
            
            # Extract userData from JSON
            if 'userData' in raw and isinstance(raw['userData'], dict):
                data['userData'] = raw['userData']

            # Try to set timing if available
            data['startTime'] = raw.get('timestamp')
            data['endTime'] = raw.get('timestamp')

        except Exception as e:
            print(f"Error parsing evaluation JSON {filepath}: {e}")
        return data
    
    @staticmethod
    def _parse_transcript_file(filepath: str, session_id: str = "unknown") -> Optional[Dict[str, Any]]:
        """Parse transcript text file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            questions = []
            responses = []
            
            # Scoring patterns for lightweight per-answer analysis (mirrors backend logic)
            patterns = {
                'empathy': (r'(empathy|empathetic|understand|understanding|compassion|compassionate|feel|feeling|emotional|emotions)', 3),
                'patience': (r'(patient|patience|calm|calmly|wait|waiting|slow|slowly|gentle|gently|take time)', 3),
                'care': (r'(care|caring|help|helping|support|supporting|assist|assisting|comfort|comforting)', 2),
                'safety': (r'(safe|safety|secure|protocol|procedure|emergency|alert|careful|cautious|report|reporting)', 4),
                'communication': (r'(listen|listening|talk|talking|explain|explaining|communicate|communication|discuss|conversation)', 2),
                'respect': (r'(respect|respectful|dignity|privacy|rights|boundaries|professional|appropriate)', 2),
                'problem_solving': (r'(solve|solution|problem|challenge|difficult|handle|manage|approach|strategy|plan)', 2),
                'experience': (r'(experience|experienced|worked|years|trained|training|certified|certification|learn|learning)', 1),
                'commitment': (r'(committed|dedication|dedicated|reliable|dependable|responsible|motivated|passion|passionate)', 2),
                'negative': (r'(angry|hate|can\'t|won\'t|never|rude|unsafe|ignore|delay|lazy|argue|frustrated|annoyed|impatient)', -3),
                'concerns': (r'(difficult|hard|struggle|struggling|stress|stressed|overwhelmed|tired|exhausted)', -1)
            }
            
            # Extract Q&A pairs - updated pattern for actual transcript format
            qa_pattern = r'Q(\d+):\s*(.+?)\n\nA\1:\s*(.+?)(?=\n\n-{40}|\n\n=|$)'
            matches = re.findall(qa_pattern, content, re.DOTALL)
            
            for match in matches:
                question_num = int(match[0])
                question_text = match[1].strip()
                answer_text = match[2].strip()
                
                questions.append({
                    "question": question_text,
                    "questionNumber": question_num,
                    "timestamp": datetime.now().isoformat()  # Would be actual timestamp in real system
                })
                
                # Lightweight analysis for highlighting
                txt = answer_text.lower()
                breakdown_counts: Dict[str, int] = {}
                score_impact: Dict[str, int] = {
                    'empathy_compassion': 0,
                    'safety_awareness': 0,
                    'communication_skills': 0,
                    'problem_solving': 0,
                    'experience_commitment': 0
                }
                flags: List[str] = []
                for key, (pat, weight) in patterns.items():
                    matches_count = len(re.findall(pat, txt, re.IGNORECASE))
                    breakdown_counts[key] = matches_count
                # Map to competencies (use counts with sign)
                score_impact['empathy_compassion'] = breakdown_counts.get('empathy', 0) + breakdown_counts.get('patience', 0) + breakdown_counts.get('care', 0)
                score_impact['safety_awareness'] = breakdown_counts.get('safety', 0)
                score_impact['communication_skills'] = breakdown_counts.get('communication', 0) + breakdown_counts.get('respect', 0)
                score_impact['problem_solving'] = breakdown_counts.get('problem_solving', 0)
                score_impact['experience_commitment'] = breakdown_counts.get('experience', 0) + breakdown_counts.get('commitment', 0)
                if breakdown_counts.get('negative', 0) > 0:
                    flags.append('negative indicators present')
                if breakdown_counts.get('concerns', 0) > 0:
                    flags.append('concerns indicators present')
                
                # Attach audio if present for this Q
                audio_url = InterviewDataService._find_audio_url(session_id, question_num)
                
                responses.append({
                    "response": answer_text,
                    "questionNumber": question_num,
                    "timestamp": datetime.now().isoformat(),
                    "analysis": {
                        "scoreImpact": score_impact,
                        "flags": flags,
                        "keyTerms": [k for k, v in breakdown_counts.items() if v > 0]
                    },
                    "audioUrl": audio_url,
                    "sessionId": session_id
                })
            
            # Build full interview audio and segments
            full_audio = InterviewDataService._get_full_audio_info(session_id, len(questions))

            # Fallback: if no per-question clips found, but full audio exists,
            # assign the full audio URL to each response and derive equal-length segments
            try:
                if full_audio and full_audio.get("url") and not any(r.get("audioUrl") for r in responses):
                    base_dir = os.path.join(os.getcwd(), INTERVIEW_OUTPUTS_DIR, 'audio')
                    fname = str(full_audio['url']).split('/')[-1]
                    fpath = os.path.join(base_dir, fname)
                    total_ms = None
                    if os.path.exists(fpath):
                        with wave.open(fpath, 'rb') as fw:
                            frames = fw.getnframes()
                            rate = fw.getframerate()
                            total_ms = int(frames / rate * 1000)
                    if total_ms is not None and len(responses) > 0:
                        n = len(responses)
                        seg_ms = max(1, total_ms // n)
                        segments: List[Dict[str, Any]] = []
                        start_ms = 0
                        for i in range(n):
                            end_ms = total_ms if i == n - 1 else min(total_ms, start_ms + seg_ms)
                            segments.append({
                                "questionNumber": i + 1,
                                "startMs": start_ms,
                                "endMs": end_ms
                            })
                            responses[i]["audioUrl"] = full_audio["url"]
                            responses[i]["audioStartMs"] = start_ms
                            responses[i]["audioEndMs"] = end_ms
                            start_ms = end_ms
                        full_audio["segments"] = segments
            except Exception:
                pass

            # Attach start/end per response when segments are known and build competencySegments
            try:
                segments_map: Dict[int, Dict[str, int]] = {}
                if full_audio and isinstance(full_audio.get("segments"), list):
                    for seg in full_audio["segments"]:
                        qn = int(seg.get("questionNumber", 0))
                        segments_map[qn] = {
                            "startMs": int(seg.get("startMs", 0)),
                            "endMs": int(seg.get("endMs", 0)),
                        }
                competency_segments: Dict[str, List[Dict[str, int]]] = {}
                for r in responses:
                    qn = int(r.get("questionNumber", 0))
                    times = segments_map.get(qn, {})
                    if times:
                        r["startMs"] = times.get("startMs", 0)
                        r["endMs"] = times.get("endMs", 0)
                    impact = (r.get("analysis", {}) or {}).get("scoreImpact", {})
                    if isinstance(impact, dict):
                        for comp_key, weight in impact.items():
                            try:
                                if isinstance(weight, int) and weight > 0:
                                    competency_segments.setdefault(comp_key, []).append({
                                        "questionNumber": qn,
                                        "startMs": times.get("startMs", 0),
                                        "endMs": times.get("endMs", 0),
                                        "weight": weight,
                                    })
                            except Exception:
                                continue
            except Exception:
                competency_segments = {}

            return {
                "sessionId": session_id,
                "questions": questions,
                "responses": responses,
                "duration": 300,  # Default duration
                "fullAudio": full_audio,
                "competencySegments": competency_segments
            }
            
        except Exception as e:
            print(f"Error parsing transcript file {filepath}: {e}")
            return None

    @staticmethod
    def _parse_transcript_json(filepath: str, session_id: str = "unknown") -> Optional[Dict[str, Any]]:
        """Parse structured JSON transcript written by FileGenerator."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Patterns for lightweight analysis
            patterns = {
                'empathy': (r'(empathy|empathetic|understand|understanding|compassion|compassionate|feel|feeling|emotional|emotions)', 3),
                'patience': (r'(patient|patience|calm|calmly|wait|waiting|slow|slowly|gentle|gently|take time)', 3),
                'care': (r'(care|caring|help|helping|support|supporting|assist|assisting|comfort|comforting)', 2),
                'safety': (r'(safe|safety|secure|protocol|procedure|emergency|alert|careful|cautious|report|reporting)', 4),
                'communication': (r'(listen|listening|talk|talking|explain|explaining|communicate|communication|discuss|conversation)', 2),
                'respect': (r'(respect|respectful|dignity|privacy|rights|boundaries|professional|appropriate)', 2),
                'problem_solving': (r'(solve|solution|problem|challenge|difficult|handle|manage|approach|strategy|plan)', 2),
                'experience': (r'(experience|experienced|worked|years|trained|training|certified|certification|learn|learning)', 1),
                'commitment': (r'(committed|dedication|dedicated|reliable|dependable|responsible|motivated|passion|passionate)', 2),
                'negative': (r'(angry|hate|can\'t|won\'t|never|rude|unsafe|ignore|delay|lazy|argue|frustrated|annoyed|impatient)', -3),
                'concerns': (r'(difficult|hard|struggle|struggling|stress|stressed|overwhelmed|tired|exhausted)', -1)
            }

            # Map audioPath (relative like audio/<file>) into API-facing audioUrl; compute analysis
            responses: List[Dict[str, Any]] = []
            for r in data.get('responses', []):
                audio_path = r.get('audioPath')
                audio_url = None
                if audio_path:
                    # Ensure we only accept real files; ignore *_sample.wav
                    base_dir = os.path.join(os.getcwd(), INTERVIEW_OUTPUTS_DIR)
                    disk_path = os.path.join(base_dir, audio_path).replace('\\', '/')
                    if disk_path.endswith('_sample.wav'):
                        audio_url = None
                    elif os.path.exists(disk_path):
                        # Serve under /outputs/<relative>
                        rel = audio_path.replace('\\', '/').lstrip('/')
                        audio_url = f"/outputs/{rel}"

                # Lightweight analysis from response text
                answer_text = (r.get('response') or '').strip()
                txt = answer_text.lower()
                breakdown_counts: Dict[str, int] = {}
                score_impact: Dict[str, int] = {
                    'empathy_compassion': 0,
                    'safety_awareness': 0,
                    'communication_skills': 0,
                    'problem_solving': 0,
                    'experience_commitment': 0
                }
                flags: List[str] = []
                for key, (pat, weight) in patterns.items():
                    matches_count = len(re.findall(pat, txt, re.IGNORECASE))
                    breakdown_counts[key] = matches_count
                score_impact['empathy_compassion'] = breakdown_counts.get('empathy', 0) + breakdown_counts.get('patience', 0) + breakdown_counts.get('care', 0)
                score_impact['safety_awareness'] = breakdown_counts.get('safety', 0)
                score_impact['communication_skills'] = breakdown_counts.get('communication', 0) + breakdown_counts.get('respect', 0)
                score_impact['problem_solving'] = breakdown_counts.get('problem_solving', 0)
                score_impact['experience_commitment'] = breakdown_counts.get('experience', 0) + breakdown_counts.get('commitment', 0)
                if breakdown_counts.get('negative', 0) > 0:
                    flags.append('negative indicators present')
                if breakdown_counts.get('concerns', 0) > 0:
                    flags.append('concerns indicators present')

                responses.append({
                    "response": r.get('response', ''),
                    "questionNumber": r.get('questionNumber'),
                    "timestamp": r.get('timestamp') or datetime.now().isoformat(),
                    "analysis": {
                        "scoreImpact": score_impact,
                        "flags": flags,
                        "keyTerms": [k for k, v in breakdown_counts.items() if v > 0]
                    },
                    "audioUrl": audio_url,
                    "sessionId": data.get('sessionId', session_id)
                })

            # Prefer real full session audio if present
            full_audio = InterviewDataService._get_full_audio_info(session_id, len(data.get('questions', [])))

            # If segments missing, derive from per-question audio durations (continuous, no silence)
            try:
                if (not full_audio) or (isinstance(full_audio, dict) and not full_audio.get('segments')):
                    base_dir = os.path.join(os.getcwd(), INTERVIEW_OUTPUTS_DIR)
                    start_ms = 0
                    segs: List[Dict[str, int]] = []
                    for qn in sorted([int(r.get('questionNumber', 0)) for r in responses if r.get('questionNumber')]):
                        # find response for qn
                        rr = next((x for x in responses if int(x.get('questionNumber', 0)) == qn), None)
                        if not rr or not rr.get('audioUrl'):
                            continue
                        fname = str(rr['audioUrl']).split('/')[-1]
                        p = os.path.join(base_dir, 'audio', fname)
                        if not os.path.exists(p):
                            continue
                        with wave.open(p, 'rb') as pw:
                            frames = pw.getnframes()
                            dur_ms = int(frames / pw.getframerate() * 1000)
                        segs.append({
                            'questionNumber': qn,
                            'startMs': start_ms,
                            'endMs': start_ms + dur_ms
                        })
                        start_ms += dur_ms  # No silence gap - continuous segments
                    if segs:
                        if not full_audio:
                            full_name = f"full_audio_{session_id}.wav"
                            full_audio = { 'url': f"/outputs/audio/{full_name}", 'segments': segs }
                        else:
                            full_audio['segments'] = segs
                        # set per-response times too
                        times_map = { s['questionNumber']: s for s in segs }
                        for r in responses:
                            qn = int(r.get('questionNumber', 0))
                            if qn in times_map:
                                r['startMs'] = times_map[qn]['startMs']
                                r['endMs'] = times_map[qn]['endMs']
            except Exception:
                pass

            return {
                "sessionId": data.get('sessionId', session_id),
                "questions": data.get('questions', []),
                "responses": responses,
                "duration": data.get('metadata', {}).get('duration', 0),
                "fullAudio": full_audio,
                "competencySegments": InterviewDataService._build_competency_segments(responses, full_audio)
            }
        except Exception as e:
            print(f"Error parsing transcript JSON {filepath}: {e}")
            return None

    @staticmethod
    def _find_audio_url(session_id: str, question_number: int) -> Optional[str]:
        """Find audio file URL for a given session and question number, if available."""
        try:
            base_dir = os.path.join(os.getcwd(), INTERVIEW_OUTPUTS_DIR, 'audio')
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            pattern = re.compile(rf'^audio_{re.escape(session_id)}_q{question_number}_.*\\.wav$', re.IGNORECASE)
            for fname in os.listdir(base_dir):
                # Ignore any previously generated sample clips
                if fname.endswith('_sample.wav'):
                    continue
                if pattern.match(fname):
                    # Served at /outputs/audio/<fname>
                    return f"/outputs/audio/{fname}"
            # No real file found
            return None
        except Exception as e:
            print(f"Error finding audio file: {e}")
            return None

    @staticmethod
    def _get_full_audio_info(session_id: str, question_count: int) -> Optional[Dict[str, Any]]:
        """Create/return a concatenated full interview audio and segment timings per question."""
        try:
            base_dir = os.path.join(os.getcwd(), INTERVIEW_OUTPUTS_DIR, 'audio')
            os.makedirs(base_dir, exist_ok=True)
            full_name = f"full_audio_{session_id}.wav"
            full_path = os.path.join(base_dir, full_name)

            # Collect per-question audio files
            part_files: List[str] = []
            segments: List[Dict[str, Any]] = []
            for q in range(1, question_count + 1):
                url = InterviewDataService._find_audio_url(session_id, q)
                if not url:
                    continue
                fname = url.split('/')[-1]
                p = os.path.join(base_dir, fname)
                if os.path.exists(p):
                    part_files.append(p)

            # If full session recording already exists (from ASGI app), prefer it
            if os.path.exists(full_path):
                start_ms = 0
                silence_ms = 250
                for idx, part in enumerate(part_files):
                    with wave.open(part, 'rb') as pw:
                        frames = pw.getnframes()
                        dur_ms = int(frames / pw.getframerate() * 1000)
                        segments.append({
                            "questionNumber": idx + 1,
                            "startMs": start_ms,
                            "endMs": start_ms + dur_ms
                        })
                        start_ms += dur_ms + (silence_ms if idx < len(part_files) - 1 else 0)
                return {
                    "url": f"/outputs/audio/{full_name}",
                    "segments": segments,
                    "sessionId": session_id
                }

            # Otherwise, build concatenated WAV (fallback)
            if not part_files:
                # No clips and no full recording: return None
                return None
            start_ms = 0
            silence_ms = 250  # 0.25s gap between answers
            silence_frames_cache: Optional[bytes] = None
            with wave.open(full_path, 'wb') as out_wav:
                # Open first file to set params
                if part_files:
                    with wave.open(part_files[0], 'rb') as w0:
                        nch, sw, fr = w0.getnchannels(), w0.getsampwidth(), w0.getframerate()
                    out_wav.setnchannels(nch)
                    out_wav.setsampwidth(sw)
                    out_wav.setframerate(fr)
                    silence_frames = int(fr * (silence_ms / 1000.0))
                    silence_frames_cache = b"\x00" * silence_frames * sw * nch
                
                for idx, part in enumerate(part_files):
                    with wave.open(part, 'rb') as pw:
                        frames = pw.getnframes()
                        data = pw.readframes(frames)
                        out_wav.writeframes(data)
                        dur_ms = int(frames / pw.getframerate() * 1000)
                        segments.append({
                            "questionNumber": idx + 1,
                            "startMs": start_ms,
                            "endMs": start_ms + dur_ms
                        })
                        start_ms += dur_ms
                    # write small silence between parts (except after last)
                    if silence_frames_cache and idx < len(part_files) - 1:
                        out_wav.writeframes(silence_frames_cache)
                        start_ms += silence_ms

            return {
                "url": f"/outputs/audio/{full_name}",
                "segments": segments,
                "sessionId": session_id
            }
        except Exception as e:
            print(f"Error building full audio: {e}")
            return None

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Interview Data API", "version": "1.0.0"}

@app.get("/api/interviews")
async def get_interviews():
    """Get all completed interviews"""
    try:
        interviews = InterviewDataService.get_all_interviews()
        return JSONResponse(content=interviews)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interviews/{session_id}")
async def get_interview(session_id: str):
    """Get specific interview by session ID"""
    try:
        interview = InterviewDataService.get_interview_by_id(session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        return JSONResponse(content=interview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interviews/{session_id}/transcript")
async def get_transcript(session_id: str):
    """Get transcript for specific interview"""
    try:
        interview = InterviewDataService.get_interview_by_id(session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        transcript = interview.get("transcript")
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return JSONResponse(content=transcript)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interviews/{session_id}/evaluation")
async def get_evaluation(session_id: str):
    """Get evaluation for specific interview"""
    try:
        interview = InterviewDataService.get_interview_by_id(session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        evaluation = interview.get("caregiverEvaluation")
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return JSONResponse(content=evaluation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
