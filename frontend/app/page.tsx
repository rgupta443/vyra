import Link from "next/link";
import { SessionDisplay } from "@/components/auth/session-display";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Instagram Content Automation</h1>
          <SessionDisplay />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-5xl font-extrabold text-gray-900 mb-6">
            AI-Powered Instagram Content Generation
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Upload your face once and generate brand-safe, Instagram-ready images with captions, hashtags, and locations. Maintain perfect identity consistency across all generations.
          </p>
          
          <div className="flex gap-4 justify-center mb-12">
            <Link
              href="/auth/signup"
              className="px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Get Started Free
            </Link>
            <Link
              href="/auth/signin"
              className="px-8 py-3 text-lg font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Sign In
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
            <div className="p-6 bg-white rounded-lg shadow-sm">
              <div className="text-3xl mb-4">🎭</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Face Identity Consistency</h3>
              <p className="text-gray-600">Upload once, maintain perfect identity across all generations with 0.95+ identity strength</p>
            </div>
            
            <div className="p-6 bg-white rounded-lg shadow-sm">
              <div className="text-3xl mb-4">✨</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Preset-Based Generation</h3>
              <p className="text-gray-600">Choose from Luxury, Lifestyle, and Beauty presets for brand-safe, professional content</p>
            </div>
            
            <div className="p-6 bg-white rounded-lg shadow-sm">
              <div className="text-3xl mb-4">📱</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Instagram-Ready Formats</h3>
              <p className="text-gray-600">9:16 Reels, 4:5 Feed, 1:1 Square - all in 4K resolution with captions and hashtags</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600">
          <p>&copy; 2026 Instagram Content Automation. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
