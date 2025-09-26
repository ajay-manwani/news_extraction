#!/usr/bin/env python3
"""
Test Google TTS with Very Long Content (10,000+ tokens)
Simulate production-length meta-summaries to find limits
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
def load_env():
    env_path = Path('/home/ajay/projects/news_extraction/.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()
sys.path.insert(0, '/home/ajay/projects/news_extraction/news_extraction_prod')

def generate_very_long_content():
    """Generate a very long news summary (~10,000 tokens)"""
    
    # Base content that we'll repeat and expand
    news_segments = [
        """Breaking news from the technology sector reveals significant developments in artificial intelligence and machine learning. Major corporations are investing billions of dollars in research and development, with particular focus on large language models and their applications across various industries. The economic impact of these investments is expected to reshape global markets over the next decade.""",
        
        """International relations continue to evolve as diplomatic efforts intensify across multiple regions. Trade agreements are being renegotiated, with emphasis on sustainable development and environmental protection. Climate change policies are driving new international partnerships and collaborative frameworks for addressing global challenges.""",
        
        """Healthcare innovations are advancing rapidly, with breakthrough discoveries in gene therapy, personalized medicine, and preventive care. Clinical trials are showing promising results for treatments of previously incurable diseases. Medical research institutions are collaborating globally to accelerate the development of new therapeutic approaches.""",
        
        """Economic indicators suggest mixed signals across global markets, with inflation rates varying significantly between developed and emerging economies. Central banking policies are being carefully calibrated to maintain stability while fostering growth. Investment patterns are shifting toward sustainable and technology-driven sectors.""",
        
        """Environmental sustainability initiatives are gaining momentum as governments and corporations implement comprehensive strategies to address climate change. Renewable energy adoption is accelerating, with solar and wind power installations reaching record levels. Carbon emission reduction targets are being revised upward as new technologies become available.""",
        
        """Educational systems worldwide are undergoing digital transformation, with remote learning technologies becoming increasingly sophisticated. Student engagement metrics show improvement when interactive technologies are properly integrated into curriculum design. Teacher training programs are evolving to incorporate these new methodologies.""",
        
        """Transportation infrastructure is being modernized to support electric vehicles and smart city initiatives. Public transit systems are implementing contactless payment solutions and real-time tracking capabilities. Urban planning strategies are prioritizing walkable communities and reduced carbon footprints.""",
        
        """Cultural exchange programs are resuming after recent global disruptions, promoting international understanding and collaboration. Art exhibitions and music festivals are incorporating technology to reach broader audiences. Digital platforms are enabling new forms of creative expression and cultural preservation.""",
        
        """Scientific research continues to push boundaries in space exploration, with multiple missions planned to explore Mars and the outer planets. Quantum computing research is making significant strides, with potential applications in cryptography, drug discovery, and climate modeling. Collaboration between academic institutions and private industry is accelerating innovation.""",
        
        """Social media platforms are implementing new privacy controls and content moderation systems in response to regulatory requirements and user concerns. Digital literacy programs are being expanded to help users navigate online environments safely. Cybersecurity measures are being strengthened to protect personal and corporate data."""
    ]
    
    # Expand each segment and create a very long summary
    expanded_content = []
    
    for i in range(50):  # Repeat and vary the content 50 times
        segment_idx = i % len(news_segments)
        base_segment = news_segments[segment_idx]
        
        # Add variation and context
        expanded_segment = f"""
        Continuing our comprehensive news coverage for today, we turn to story number {i + 1}. {base_segment}
        
        Furthermore, industry experts are analyzing the long-term implications of these developments, considering factors such as regulatory compliance, market dynamics, and consumer behavior patterns. Stakeholder engagement is critical for successful implementation of these initiatives.
        
        Market analysts predict that these trends will continue to influence investment decisions and strategic planning across multiple sectors. The interconnected nature of global systems means that developments in one region often have cascading effects worldwide.
        
        Looking ahead, sustainable growth models are being prioritized by both public and private sector organizations. Innovation frameworks are being established to support emerging technologies while ensuring ethical considerations are properly addressed.
        """
        
        expanded_content.append(expanded_segment.strip())
    
    # Create the final very long content
    long_content = f"""
    Welcome to our comprehensive daily news podcast for {os.getenv('DATE', 'September 26th, 2025')}. This extended edition covers major developments across all sectors with detailed analysis and expert commentary.
    
    {' '.join(expanded_content)}
    
    This concludes our extended news coverage. We've covered {len(expanded_content)} major stories with comprehensive analysis and expert insights. Thank you for your attention to this detailed news briefing. We'll continue monitoring these developments and provide updates as new information becomes available.
    
    Remember to stay informed, stay engaged, and we'll see you again tomorrow for another comprehensive news update covering all the important developments from around the world.
    """
    
    return long_content.strip()

def test_long_content_limits():
    """Test Google TTS with various content lengths to find the limit"""
    print("📏 Testing Google TTS with Very Long Content")
    print("=" * 60)
    
    try:
        from src.tts_generator import TTSGenerator
        
        # Force production environment
        os.environ['ENVIRONMENT'] = 'production'
        
        tts = TTSGenerator()
        
        if not tts.google_tts_available:
            print("❌ Google TTS not available")
            return
        
        # Generate very long content
        long_content = generate_very_long_content()
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(long_content) // 4
        
        print(f"📊 Generated content stats:")
        print(f"   Characters: {len(long_content):,}")
        print(f"   Estimated tokens: {estimated_tokens:,}")
        print(f"   Words (approx): {len(long_content.split()):,}")
        print()
        
        # Test with different content lengths
        test_lengths = [
            (500, "500 chars (very short)"),
            (2000, "2,000 chars (short)"),
            (5000, "5,000 chars (medium)"),
            (10000, "10,000 chars (long)"),
            (20000, "20,000 chars (very long)"),
            (len(long_content), f"Full content ({len(long_content):,} chars)")
        ]
        
        successful_length = 0
        
        for length, description in test_lengths:
            if length > len(long_content):
                continue
                
            test_content = long_content[:length]
            tokens = length // 4
            
            print(f"🧪 Testing {description} (~{tokens:,} tokens)")
            print(f"   Preview: {test_content[:100]}...")
            
            try:
                result = tts.generate_speech(test_content, use_premium=True)
                
                if result and os.path.exists(result):
                    file_size = os.path.getsize(result) / 1024 / 1024  # MB
                    print(f"   ✅ SUCCESS: {result}")
                    print(f"   📏 Audio file: {file_size:.1f} MB")
                    successful_length = length
                else:
                    print(f"   ❌ FAILED: No result file")
                    break
                    
            except Exception as e:
                print(f"   💥 ERROR: {str(e)}")
                if "400" in str(e) or "Bad Request" in str(e):
                    print(f"   🚨 Hit Google TTS limit at {length:,} characters (~{tokens:,} tokens)")
                break
            
            print()
        
        print("=" * 60)
        print("📋 SUMMARY:")
        print(f"✅ Maximum successful length: {successful_length:,} characters")
        print(f"🎯 Estimated token limit: ~{successful_length // 4:,} tokens")
        
        # Check if this explains the production failure
        if successful_length < 15000:  # If limit is less than typical production content
            print()
            print("🔍 CONCLUSION:")
            print("This likely explains the production failure!")
            print("Production meta-summaries are probably exceeding Google TTS limits.")
            print("Solution needed: Split long content into chunks.")
        
    except Exception as e:
        print(f"💥 Setup error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_long_content_limits()