import React, { useState } from 'react';
import {
  Container,
  Row,
  Col,
  Form,
  Button,
  InputGroup,
  Alert,
  Spinner
} from 'react-bootstrap';
import './bootstrap.css';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [images, setImages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Handle changes to the input field storing the URL
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(event.target.value);
  };

  // Scrape images based on the entered URL
  const handleScrape = async () => {
    setError(null);
    setImages([]);
    setDownloadUrl(null);

    if (url) {
      setIsLoading(true);
      try {
        const response = await fetch('http://127.0.0.1:8000/api/scrape/images?url=' + url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) throw new Error('Failed to scrape the URL.');

        const data = await response.json();
        const resultDownloadUrl = data['Images are available for download at'];
        setDownloadUrl(resultDownloadUrl);

        // Fetch images from the newly provided download URL
        const imageResponse = await fetch(resultDownloadUrl);
        if (!imageResponse.ok) throw new Error('Failed to retrieve images.');

        const imageData = await imageResponse.json();
        console.log('Fetched images:', imageData.images);
        setImages(imageData.images || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    } else {
      setError('Please enter a URL.');
    }
  };

  return (
    <Container fluid className="py-5">
      <Row className="justify-content-center">
        <Col xs={12} md={8} lg={6} className="mb-4">
          <h1 className="text-center mb-4">Scrape It</h1>

          <InputGroup className="mb-3">
            <Form.Control
              type="text"
              placeholder="Enter URL"
              value={url}
              onChange={handleInputChange}
              aria-label="URL"
            />
            <Button variant="primary" onClick={handleScrape}>
              Scrape
            </Button>
          </InputGroup>

          {error && <Alert variant="danger">{error}</Alert>}

          {isLoading && (
            <div className="d-flex justify-content-center align-items-center my-3">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Scraping...</span>
              </Spinner>
            </div>
          )}

          {downloadUrl && (
            <Alert variant="info" className="mt-3">
              <p className="mb-1">Images are available for download at:</p>
              <a href={downloadUrl} target="_blank" rel="noopener noreferrer">
                {downloadUrl}
              </a>
            </Alert>
          )}
        </Col>
      </Row>

      {images.length > 0 && (
        <Row className="g-3 justify-content-center">
          {images.map((imageUrl, index) => (
            <Col xs={12} sm={6} md={4} lg={3} key={index}>
              <img
                className="img-fluid"
                src={imageUrl}
                alt={`Scraped image ${index + 1}`}
                onError={(e) => {
                  console.error(`Image failed to load: ${imageUrl}`);
                  e.currentTarget.style.display = 'none';
                }}
              />
            </Col>
          ))}
        </Row>
      )}
    </Container>
  );
}

export default App;
