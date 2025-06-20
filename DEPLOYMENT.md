# Deployment Guide

This guide covers deploying the Company Research API to various free cloud platforms.

## Prerequisites

### Required API Keys
You'll need the following API keys:
- `OPENAI_API_KEY` - OpenAI API key for LLM processing
- `APOLLO_API_KEY` - Apollo.io API key for company data
- `CORESIGNAL_API_KEY` - CoreSignal API key for additional company data
- `TAVILY_API_KEY` - Tavily Search API key for web search

### Optional Google Drive Setup
If you want Google Drive upload functionality:
- Set up a Google Cloud Project
- Enable Google Drive API
- Create a service account and download `service_account.json`
- Place the file in the project root (already in .gitignore)

### Optional Email Setup
For email notifications and report delivery:
- Set up an email account (Gmail recommended)
- For Gmail: Enable 2-factor authentication and create an App Password
- Set the following environment variables:
  - `EMAIL_USER`: Your email address
  - `EMAIL_PASSWORD`: Your email password or app password
  - `SMTP_SERVER`: SMTP server (smtp.gmail.com for Gmail)
  - `SMTP_PORT`: SMTP port (587 for Gmail)

## Deployment Options

### 1. Railway (Recommended)

Railway offers a generous free tier and easy GitHub integration.

#### Steps:
1. **Push your code to GitHub** (if not already done)
2. **Sign up for Railway**: https://railway.app/
3. **Connect your GitHub repository**
4. **Deploy from GitHub**:
   - Select your repository
   - Railway will automatically detect the Dockerfile
5. **Set environment variables** in Railway dashboard:
   ```
   APOLLO_API_KEY=your_apollo_key
   CORESIGNAL_API_KEY=your_coresignal_key
   TAVILY_API_KEY=your_tavily_key
   OPENAI_API_KEY=your_openai_key
   ```
6. **Deploy** - Railway will build and deploy automatically

**Free Tier**: $5 credit per month, auto-sleep after inactivity

#### Key Features Available:
- **Web Interface**: User-friendly frontend at `/` for easy report generation
- **Background Processing**: Use `/api/*-background` endpoints for non-blocking operations
- **Email Notifications**: Automatic email delivery with PDF attachments and Drive links
- **Auto Company Name Extraction**: No need to manually enter company names
- **All API endpoints under `/api` prefix** for better organization

### 2. Render

#### Steps:
1. **Sign up for Render**: https://render.com/
2. **Connect your GitHub repository**
3. **Create a new Web Service**
4. **Use the following settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.company_research_fastapi:app --host 0.0.0.0 --port $PORT`
5. **Set environment variables** in Render dashboard
6. **Deploy**

**Free Tier**: 750 hours per month, auto-sleep after 15 minutes

### 3. Fly.io

#### Steps:
1. **Install flyctl**: https://fly.io/docs/getting-started/installing-flyctl/
2. **Sign up and login**:
   ```bash
   fly auth signup
   fly auth login
   ```
3. **Deploy**:
   ```bash
   fly launch
   # Follow the prompts, use the existing fly.toml
   ```
4. **Set environment variables**:
   ```bash
   fly secrets set APOLLO_API_KEY=your_apollo_key
   fly secrets set CORESIGNAL_API_KEY=your_coresignal_key
   fly secrets set TAVILY_API_KEY=your_tavily_key
   fly secrets set OPENAI_API_KEY=your_openai_key
   ```
5. **Deploy**:
   ```bash
   fly deploy
   ```

**Free Tier**: $5 credit per month, auto-scale to zero

### 4. Vercel (Limitations)

⚠️ **Note**: Vercel has limitations for this application:
- 10-second execution limit (may not work for long research tasks)
- Limited system packages (pandoc may not work for PDF generation)

#### Steps:
1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```
2. **Deploy**:
   ```bash
   vercel
   ```
3. **Set environment variables** in Vercel dashboard

## Environment Variables Reference

| Variable                           | Required | Description                                                    |
| ---------------------------------- | -------- | -------------------------------------------------------------- |
| `OPENAI_API_KEY`                   | Yes      | OpenAI API key for LLM processing                              |
| `APOLLO_API_KEY`                   | Yes      | Apollo.io API key                                              |
| `CORESIGNAL_API_KEY`               | Yes      | CoreSignal API key                                             |
| `TAVILY_API_KEY`                   | Yes      | Tavily Search API key                                          |
| `EMAIL_USER`                       | No       | Email address for sending reports (e.g., your-email@gmail.com) |
| `EMAIL_PASSWORD`                   | No       | Email password or app password for Gmail                       |
| `SMTP_SERVER`                      | No       | SMTP server (default: smtp.gmail.com)                          |
| `SMTP_PORT`                        | No       | SMTP port (default: 587)                                       |
| `GOOGLE_DRIVE_FOLDER_ID`           | No       | Google Drive folder ID for uploads                             |
| `GOOGLE_DRIVE_INTERFACE_FOLDER_ID` | No       | Google Drive folder ID for web interface uploads               |
| `APOLLO_BASE_URL`                  | No       | Apollo API base URL (default: https://api.apollo.io/api/v1)    |
| `CORESIGNAL_BASE_URL`              | No       | CoreSignal API base URL (default: https://api.coresignal.com)  |

## Testing Your Deployment

Once deployed, test your API:

1. **Health Check**:
   ```bash
   curl https://your-app-url.com/api/health
   ```

2. **Web Interface**:
   Visit `https://your-app-url.com/` for the user-friendly web interface

3. **API Documentation**:
   Visit `https://your-app-url.com/docs` for interactive API documentation

4. **Sample Multi-Source Research Request**:
   ```bash
   curl -X POST "https://your-app-url.com/api/multi-source-research" \
   -H "Content-Type: application/json" \
   -d '{
     "domain": "openai.com",
     "return_data": true,
     "upload_to_drive": false
   }'
   ```

5. **Sample Background Research Request**:
   ```bash
   curl -X POST "https://your-app-url.com/api/multi-source-research-background" \
   -H "Content-Type: application/json" \
   -d '{
     "website": "https://openai.com",
     "email": "your-email@example.com"
   }'
   ```

6. **Sample CoreSignal PDF Generation**:
   ```bash
   curl -X POST "https://your-app-url.com/api/coresignal/generate-pdf" \
   -H "Content-Type: application/json" \
   -d '{
     "website": "https://openai.com",
     "upload_to_drive": false
   }'
   ```

## Monitoring and Logs

The application uses Python's built-in logging system with the following features:

- **Structured Logging**: All logs include timestamps, module names, and log levels
- **Request Logging**: HTTP requests are automatically logged with duration and status codes
- **API Operations**: All major operations (data fetching, PDF generation, uploads) are logged
- **Error Tracking**: Errors include full context and stack traces

### Viewing Logs by Platform:

- **Railway**: View logs in Railway dashboard → Service → Logs tab
- **Render**: Check Render dashboard → Service → Logs tab  
- **Fly.io**: Use `fly logs` command
- **Docker Local**: Use `docker-compose logs -f` or `docker logs -f <container>`

## Troubleshooting

### Common Issues:

1. **Missing API Keys**: Check the `/api/health` endpoint to verify all API keys are set
2. **404 Errors on API Calls**: Ensure you're using the `/api` prefix for all API endpoints (e.g., `/api/multi-source-research` not `/multi-source-research`)
3. **Company Name Not Found**: The system now automatically extracts company names from domain data - no need to provide manually
4. **PDF Generation Issues**: Some platforms may not support pandoc - consider disabling PDF generation
5. **Memory Issues**: The application may need more memory for large requests
6. **Timeout Issues**: Long research tasks may timeout on platforms with execution limits - use background endpoints for long-running tasks
7. **Email Issues**: Check that all email environment variables are set correctly for email functionality

### Logs:
- **Railway**: Check logs in Railway dashboard
- **Render**: Check logs in Render dashboard  
- **Fly.io**: `fly logs`
- **Vercel**: Check function logs in Vercel dashboard

## Production Considerations

1. **Rate Limiting**: Consider implementing rate limiting for production use
2. **Caching**: Add caching for repeated requests
3. **Database**: For storing results, consider adding a database
4. **Monitoring**: Set up monitoring and alerts
5. **Scaling**: For high traffic, consider paid tiers with auto-scaling

## Security Notes

- Never commit API keys to the repository
- Use environment variables for all sensitive data
- Consider implementing authentication for production use
- The `service_account.json` file is in .gitignore - never commit it 