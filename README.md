# Price Grabber
RVCC Capstone project created by Sharanya Ram.

This program seeks to help users understand how 
product prices vary across different platforms. 
Those exhibited in the application are Walmart, Amazon, and Target. 
There are 20 popular electronics products used as the testing baseline.

## Installation
In order to run the interactive dashboard, clone the repository and install Docker Desktop.

## Run with Docker

### Prerequisites

- Docker Desktop installed and running

### Install and run

1. Clone the repository and open its folder:

   ```powershell
   git clone https://github.com/sram-coder/price-tracker.git 
   cd price-tracker
   ```

2. Build the Docker image:

   ```powershell
   docker build -t price-tracker:latest .
   ```

3. Start the app:

   ```powershell
   docker run -d --name price-tracker -p 5001:5000 price-tracker:latest
   ```

4. Open [http://localhost:5001](http://localhost:5001) in your browser.

The port mapping sends traffic from port `5001` on your computer to port `5000` in the container. If port `5001` is already in use, change the left-hand port—for example, `5002:5000`—and visit `http://localhost:5002`. <citation src="1,3"></citation>

### Stop the dashboard

```powershell
docker stop price-tracker
docker rm price-tracker
```
