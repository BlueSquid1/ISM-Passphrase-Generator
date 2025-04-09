# Use the official Go image as the base image
FROM golang:1.24.1-alpine3.21 AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy the Go modules manifests
COPY server/go.mod server/go.sum ./server/

# Download Go module dependencies
RUN cd server && go mod download

# install go command tools
RUN go install golang.org/x/tools/cmd/stringer@v0.31.0

# Copy the source code into the container
COPY server/ ./server/

# Build the Go application
RUN cd server && go generate ./passphaseMgr/classifications.go && go build -o passphrase-generator

# Use a minimal base image for the final container
FROM alpine:3.21

# Set the working directory inside the container
WORKDIR /app

COPY client client

COPY server/data server/data 

# Copy the compiled binary from the builder stage
COPY --from=builder /app/server/passphrase-generator ./server/

WORKDIR /app/server

EXPOSE 8080

# Command to run the application
CMD ["./passphrase-generator"]
