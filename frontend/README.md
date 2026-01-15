# Instagram Content Automation - Frontend

Next.js frontend application for the Instagram Content Automation platform.

## Features

- **Authentication**: Email/password and Google OAuth sign-in
- **Face Upload**: Upload and manage face images for identity consistency
- **Content Generation**: Select presets and formats to generate Instagram-ready content
- **Results Dashboard**: View generated images with captions, hashtags, and locations
- **Export Tools**: Download images and copy content for Instagram posting
- **Generation History**: Browse all past generations

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Styling**: Tailwind CSS
- **Authentication**: NextAuth.js v5 (beta)
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **TypeScript**: Full type safety

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.local.example .env.local
   ```

   Edit `.env.local` with your configuration:
   ```env
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your-secret-key-change-this
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── api/auth/            # NextAuth.js API routes
│   ├── auth/                # Authentication pages (signin, signup)
│   ├── dashboard/           # User dashboard
│   ├── generate/            # Content generation interface
│   ├── history/             # Generation history
│   ├── results/[jobId]/     # Individual result page
│   ├── layout.tsx           # Root layout with providers
│   └── page.tsx             # Landing page
├── components/              # Reusable React components
│   ├── auth/               # Authentication components
│   ├── face/               # Face upload components
│   └── export/             # Export functionality components
├── lib/                     # Utility libraries
│   ├── api.ts              # Axios API client
│   └── providers.tsx       # React Query & NextAuth providers
├── types/                   # TypeScript type definitions
│   └── next-auth.d.ts      # NextAuth type extensions
├── auth.ts                  # NextAuth configuration
└── middleware.ts            # Route protection middleware
```

## Key Pages

### Landing Page (`/`)
- Marketing homepage with feature highlights
- Sign in/sign up CTAs
- Session display in header

### Authentication (`/auth/signin`, `/auth/signup`)
- Email/password authentication
- Google OAuth integration
- Form validation and error handling

### Dashboard (`/dashboard`)
- Face management (upload/remove)
- Quick stats display
- Navigation to generation interface

### Generate (`/generate`)
- Preset selection (Luxury, Lifestyle, Beauty)
- Format selection (9:16, 4:5, 1:1)
- Generation request submission

### Results (`/results/[jobId]`)
- Real-time status updates
- Generated image display
- Caption, hashtags, and location display
- Export functionality (download, copy)

### History (`/history`)
- Grid view of all generations
- Click to view individual results

## API Integration

The frontend communicates with the FastAPI backend through the Axios client configured in `lib/api.ts`.

### Authentication
- Tokens are managed by NextAuth.js
- API requests include `Authorization: Bearer {token}` header

### Endpoints Used
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /faces/upload` - Face upload
- `GET /faces/current` - Get current face
- `DELETE /faces/current` - Remove face
- `POST /generate/image` - Start generation
- `GET /generate/status/{job_id}` - Check generation status
- `GET /generate/history` - Get generation history

## Development

### Build for Production
```bash
npm run build
```

### Start Production Server
```bash
npm start
```

### Linting
```bash
npm run lint
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXTAUTH_URL` | Application URL | Yes |
| `NEXTAUTH_SECRET` | Secret for session encryption | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes (for OAuth) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes (for OAuth) |
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |

## Protected Routes

The following routes require authentication (configured in `middleware.ts`):
- `/dashboard/*`
- `/generate/*`
- `/profile/*`

Unauthenticated users are redirected to `/auth/signin`.

## Features Implementation

### Face Upload
- File validation (type, size)
- Image preview
- Progress tracking
- Success/error feedback

### Content Generation
- Preset selection UI
- Format selection UI
- Real-time generation status
- Error handling with user feedback

### Export Functionality
- Download images in original resolution
- Copy caption to clipboard
- Copy hashtags to clipboard
- Copy all content formatted for Instagram

### Real-time Updates
- Polling for generation status
- Automatic UI updates
- Loading states and animations

## Styling

The application uses Tailwind CSS for styling with a clean, modern design:
- Responsive layouts for mobile and desktop
- Consistent color scheme (blue primary, gray neutrals)
- Smooth transitions and hover effects
- Accessible form inputs and buttons

## Future Enhancements

- [ ] Add toast notifications instead of alerts
- [ ] Implement image editing tools
- [ ] Add batch generation support
- [ ] Create mobile app version
- [ ] Add social sharing features
- [ ] Implement analytics dashboard

## License

[Add your license here]
