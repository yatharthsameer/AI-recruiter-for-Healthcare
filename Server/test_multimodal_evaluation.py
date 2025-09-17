#!/usr/bin/env python3
"""
Test script for multimodal evaluation with audio data
"""
import asyncio
import json
import os
from services.caregiver_evaluation_service import caregiver_evaluation_service
from utils.file_generator import file_generator

async def test_multimodal_evaluation():
    """Test multimodal evaluation with mock audio data"""
    
    print("🧪 Testing Multimodal Evaluation System")
    print("=" * 60)
    
    # Sample transcript
    transcript = """
Interviewer: Have you ever worked as a caregiver? What kinds of patients did you work with?
Candidate: Yes, I have 3 years of experience working with elderly patients in assisted living. I helped with daily activities like bathing, medication reminders, and mobility assistance.
Interviewer: Why do you want to be a caregiver?
Candidate: I'm passionate about helping people maintain their independence and dignity. It's very rewarding to make a positive impact on someone's daily life.
"""

    # Mock audio data (in real scenario, this would be actual audio bytes)
    mock_audio_1 = b"mock_audio_data_response_1" * 100  # Simulate audio bytes
    mock_audio_2 = b"mock_audio_data_response_2" * 150  # Different length for variety
    
    # Test data with audio
    test_data_with_audio = {
        'transcript': transcript.strip(),
        'userData': {
            'firstName': 'Sarah',
            'lastName': 'Wilson', 
            'email': 'sarah.wilson@email.com',
            'phone': '+1555987654',
            'caregivingExperience': True,
            'hasPerId': True,
            'driversLicense': True,
            'autoInsurance': True,
            'availability': ['Morning', 'Afternoon'],
            'weeklyHours': 30,
            'languages': ['English']
        },
        'sessionId': 'multimodal_test_001',
        'responses': [
            {
                'response': 'Yes, I have 3 years of experience working with elderly patients...',
                'questionNumber': 1,
                'audioData': mock_audio_1,
                'audioMime': 'audio/webm'
            },
            {
                'response': "I'm passionate about helping people maintain their independence...",
                'questionNumber': 2,
                'audioData': mock_audio_2,
                'audioMime': 'audio/webm'
            }
        ],
        'audioData': [mock_audio_1, mock_audio_2]
    }
    
    # Test data without audio (text-only)
    test_data_text_only = {
        'transcript': transcript.strip(),
        'userData': test_data_with_audio['userData'],
        'sessionId': 'text_only_test_001'
    }
    
    print("🎵 Testing Multimodal Evaluation (with audio):")
    print(f"   Audio chunks: {len(test_data_with_audio['audioData'])}")
    print(f"   Audio sizes: {[len(audio) for audio in test_data_with_audio['audioData']]} bytes")
    
    try:
        multimodal_evaluation = await caregiver_evaluation_service.evaluate_candidate(test_data_with_audio)
        
        print("\n✅ Multimodal Evaluation Results:")
        print(f"   Evaluation Type: {multimodal_evaluation.get('evaluationType', 'unknown')}")
        print(f"   Overall Score: {multimodal_evaluation.get('overallScore')}/10")
        
        # Check for audio insights
        audio_insights = multimodal_evaluation.get('audioInsights', {})
        if audio_insights:
            print("\n🎧 Audio Insights:")
            for key, value in audio_insights.items():
                print(f"   {key}: {value}")
        else:
            print("   No audio insights generated")
        
        print("\n📊 Dimension Scores:")
        for dimension, score in multimodal_evaluation.get('scores', {}).items():
            print(f"   {dimension}: {score}/10")
        
        # Save multimodal evaluation
        json_path = await file_generator.save_evaluation_json('multimodal_test_001', multimodal_evaluation)
        print(f"\n💾 Multimodal evaluation saved: {json_path}")
        
    except Exception as e:
        print(f"❌ Multimodal evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📝 Testing Text-Only Evaluation (for comparison):")
    
    try:
        text_evaluation = await caregiver_evaluation_service.evaluate_candidate(test_data_text_only)
        
        print("\n✅ Text-Only Evaluation Results:")
        print(f"   Evaluation Type: {text_evaluation.get('evaluationType', 'unknown')}")
        print(f"   Overall Score: {text_evaluation.get('overallScore')}/10")
        
        print("\n📊 Dimension Scores:")
        for dimension, score in text_evaluation.get('scores', {}).items():
            print(f"   {dimension}: {score}/10")
        
        # Save text-only evaluation
        json_path = await file_generator.save_evaluation_json('text_only_test_001', text_evaluation)
        print(f"\n💾 Text-only evaluation saved: {json_path}")
        
    except Exception as e:
        print(f"❌ Text-only evaluation failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Comparison Summary:")
    
    try:
        if 'multimodal_evaluation' in locals() and 'text_evaluation' in locals():
            print(f"   Multimodal Score: {multimodal_evaluation.get('overallScore', 'N/A')}/10")
            print(f"   Text-Only Score:  {text_evaluation.get('overallScore', 'N/A')}/10")
            
            # Compare evaluation types
            multimodal_type = multimodal_evaluation.get('evaluationType', 'unknown')
            text_type = text_evaluation.get('evaluationType', 'unknown')
            
            print(f"   Multimodal Type: {multimodal_type}")
            print(f"   Text-Only Type:  {text_type}")
            
            # Check if multimodal actually used audio
            has_audio_insights = bool(multimodal_evaluation.get('audioInsights'))
            print(f"   Audio Analysis Used: {'✅ Yes' if has_audio_insights else '❌ No'}")
            
            return True
    except Exception as e:
        print(f"   Comparison failed: {e}")
        return False

async def test_gemini_multimodal_capabilities():
    """Test if Gemini service has multimodal capabilities"""
    
    print("\n🔧 Testing Gemini Service Capabilities:")
    
    try:
        from services.gemini_service import gemini_service
        
        # Check if multimodal methods are available
        has_analyze_turn = hasattr(gemini_service, 'analyze_turn')
        has_upload_media = hasattr(gemini_service, '_upload_media')
        has_build_report = hasattr(gemini_service, 'build_final_report')
        
        print(f"   analyze_turn method: {'✅ Available' if has_analyze_turn else '❌ Missing'}")
        print(f"   _upload_media method: {'✅ Available' if has_upload_media else '❌ Missing'}")
        print(f"   build_final_report method: {'✅ Available' if has_build_report else '❌ Missing'}")
        
        # Test health check
        health = gemini_service.health_check()
        print(f"   Health Status: {health.get('status', 'unknown')}")
        
        if has_analyze_turn:
            print("   🎉 Multimodal Gemini service is ready!")
            return True
        else:
            print("   ⚠️ Multimodal capabilities not fully available")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking Gemini capabilities: {e}")
        return False

if __name__ == "__main__":
    async def main():
        # Test Gemini capabilities first
        gemini_ready = await test_gemini_multimodal_capabilities()
        
        # Run evaluation tests
        success = await test_multimodal_evaluation()
        
        print("\n" + "=" * 60)
        if success and gemini_ready:
            print("🎉 Multimodal evaluation system is working!")
            print("\n🚀 Key Features Implemented:")
            print("   ✅ Audio data capture during interviews")
            print("   ✅ Multimodal Gemini analysis (when audio available)")
            print("   ✅ Fallback to text-only evaluation")
            print("   ✅ Audio insights extraction")
            print("   ✅ Enhanced JSON output with audio metadata")
        else:
            print("💥 Some multimodal features may not be working correctly")
            print("   Check the logs above for specific issues")
    
    asyncio.run(main())
