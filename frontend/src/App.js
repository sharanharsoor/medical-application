import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Tab, Tabs, Container, Card, Button, Spinner, Form, Badge, ListGroup, Alert } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import config from './config';

const API_BASE_URL = config.apiUrl;
const PING_INTERVAL = 4 * 60 * 1000; // 4 minutes

const styles = {
  container: {
    backgroundColor: '#f0f7ff',
    minHeight: '100vh',
    padding: '20px 0'
  },
  header: {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '20px',
    borderRadius: '10px',
    marginBottom: '20px',
    textAlign: 'center'
  },
  querySection: {
    backgroundColor: '#ffffff',
    padding: '25px',
    borderRadius: '12px',
    marginBottom: '20px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
  },
  analysisCard: {
    backgroundColor: '#ffffff',
    borderRadius: '10px',
    marginBottom: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  tabContent: {
    backgroundColor: '#ffffff',
    padding: '20px',
    borderRadius: '10px',
    marginTop: '10px'
  },
  submitButton: {
    background: 'linear-gradient(135deg, #1e88e5 0%, #1565c0 100%)',
    border: 'none',
    padding: '10px 25px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  analysisText: {
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#2c3e50'
  }
};

function App() {
  const [latestAnalyses, setLatestAnalyses] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [dateAnalyses, setDateAnalyses] = useState(null);
  const [stats, setStats] = useState(null);
  const [query, setQuery] = useState('');
  const [queryResponse, setQueryResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [nextUpdate, setNextUpdate] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Refs for cleanup
  const abortControllerRef = useRef(null);
  const statusIntervalRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  // Keep-alive ping function
  const pingServer = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        console.warn('Keep-alive ping failed, status:', response.status);
      }
    } catch (err) {
      console.warn('Keep-alive ping failed:', err);
    }
  }, []);

  // Enhanced API call wrapper
  const fetchWithRetry = useCallback(async (url, options = {}, retries = 3) => {
    let attempt = 0;

    while (attempt < retries) {
      try {
        abortControllerRef.current = new AbortController();
        const signal = abortControllerRef.current.signal;

        const response = await fetch(url, {
          ...options,
          signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          }
        });

        if (!response.ok) {
          throw new Error(await response.text());
        }

        return await response.json();
      } catch (err) {
        attempt++;
        if (err.name === 'AbortError' || attempt === retries) {
          throw err;
        }
        await new Promise(resolve => {
          retryTimeoutRef.current = setTimeout(resolve, Math.pow(2, attempt) * 1000);
        });
      }
    }
  }, []);

  const cancelPendingRequests = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
  }, []);

  const fetchWithLoadingState = useCallback(async (fetchFn) => {
    try {
      setLoading(true);
      setError(null);
      await fetchFn();
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchInitialStatus = useCallback(async () => {
    const data = await fetchWithRetry(`${API_BASE_URL}/scheduler/initial-check`);
    setNextUpdate(data.message);
    setIsInitializing(false);
  }, [fetchWithRetry]);

  const fetchSchedulerStatus = useCallback(async () => {
    const data = await fetchWithRetry(`${API_BASE_URL}/scheduler/status`);
    setSchedulerStatus(data);
  }, [fetchWithRetry]);

  const fetchLatestAnalyses = useCallback(async () => {
    const data = await fetchWithRetry(`${API_BASE_URL}/analyses/latest`);
    setLatestAnalyses(data);
  }, [fetchWithRetry]);

  const fetchAvailableDates = useCallback(async () => {
    const data = await fetchWithRetry(`${API_BASE_URL}/analyses/dates`);
    setAvailableDates(data);
  }, [fetchWithRetry]);

  const fetchAnalysesByDate = useCallback(async (date) => {
    const data = await fetchWithRetry(`${API_BASE_URL}/analyses/${date}`);
    setDateAnalyses(data);
  }, [fetchWithRetry]);

  const fetchStats = useCallback(async () => {
    const data = await fetchWithRetry(`${API_BASE_URL}/analyses/stats/summary`);
    setStats(data);
  }, [fetchWithRetry]);

  // Keep-alive effect
  useEffect(() => {
    pingServer(); // Initial ping
    pingIntervalRef.current = setInterval(pingServer, PING_INTERVAL);

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [pingServer]);

  // Initialize app data
  useEffect(() => {
    const initializeApp = async () => {
      await fetchWithLoadingState(async () => {
        await Promise.all([
          fetchInitialStatus(),
          fetchLatestAnalyses(),
          fetchAvailableDates(),
          fetchStats(),
          fetchSchedulerStatus()
        ]);
      });

      statusIntervalRef.current = setInterval(() => {
        fetchSchedulerStatus().catch(console.error);
      }, 60000);
    };

    initializeApp();

    return () => {
      cancelPendingRequests();
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [fetchInitialStatus, fetchLatestAnalyses, fetchAvailableDates, fetchStats, fetchSchedulerStatus, fetchWithLoadingState, cancelPendingRequests]);

  const submitQuery = async (e) => {
    e.preventDefault();
    await fetchWithLoadingState(async () => {
      const data = await fetchWithRetry(`${API_BASE_URL}/query`, {
        method: 'POST',
        body: JSON.stringify({ text: query }),
      });
      setQueryResponse(data);
    });
  };

  const triggerManualUpdate = async () => {
    await fetchWithLoadingState(async () => {
      await fetchWithRetry(`${API_BASE_URL}/update-analyses`, {
        method: 'POST',
      });
      await Promise.all([
        fetchLatestAnalyses(),
        fetchAvailableDates(),
        fetchStats()
      ]);
    });
  };

  const renderAnalysis = useCallback((analysis) => {
    if (!analysis) return null;

    const formattedText = analysis
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />');

    return (
      <Card style={styles.analysisCard}>
        <Card.Body>
          <div
            className="analysis-content"
            style={styles.analysisText}
            dangerouslySetInnerHTML={{ __html: formattedText }}
          />
        </Card.Body>
      </Card>
    );
  }, []);

  if (isInitializing) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Container>
        <div style={styles.header}>
          <h1>Medical Research Assistant</h1>
          {nextUpdate && (
            <small className="text-light">
              {nextUpdate}
            </small>
          )}
        </div>

        {error && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible>
            {error}
          </Alert>
        )}

        <Tabs defaultActiveKey="query" id="main-tabs" className="mb-4">
          <Tab eventKey="query" title="Ask a Question">
            <div style={styles.querySection}>
              <h3 className="mb-4">Ask Your Medical Research Question</h3>
              <Form onSubmit={submitQuery}>
                <Form.Group className="mb-3">
                  <Form.Control
                    as="textarea"
                    rows={3}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter your medical research question..."
                    style={{ fontSize: '16px' }}
                  />
                </Form.Group>
                <Button
                  type="submit"
                  disabled={loading}
                  style={styles.submitButton}
                >
                  {loading ? <Spinner size="sm" /> : 'Submit Query'}
                </Button>
              </Form>

              {queryResponse && (
                <Card className="mt-4">
                  <Card.Body>
                    <Card.Title>Response</Card.Title>
                    {renderAnalysis(queryResponse.response)}
                  </Card.Body>
                </Card>
              )}
            </div>
          </Tab>

          <Tab eventKey="latest" title="Latest Analyses">
            {loading ? (
              <div className="text-center p-4">
                <Spinner animation="border" />
              </div>
            ) : latestAnalyses ? (
              <div style={styles.tabContent}>
                <h3>Date: {latestAnalyses.date}</h3>
                <Tabs>
                  <Tab eventKey="trends" title="Recent Trends">
                    {renderAnalysis(latestAnalyses.recent_trends)}
                  </Tab>
                  <Tab eventKey="clinical" title="Clinical">
                    {renderAnalysis(latestAnalyses.clinical)}
                  </Tab>
                  <Tab eventKey="research" title="Research">
                    {renderAnalysis(latestAnalyses.research)}
                  </Tab>
                </Tabs>
              </div>
            ) : null}
          </Tab>

          <Tab eventKey="historical" title="Historical Data">
            <div style={styles.tabContent}>
              <Form.Select
                className="mb-3"
                onChange={(e) => {
                  setSelectedDate(e.target.value);
                  if (e.target.value) {
                    fetchWithLoadingState(() => fetchAnalysesByDate(e.target.value));
                  }
                }}
              >
                <option value="">Select a date...</option>
                {availableDates.map(date => (
                  <option key={date} value={date}>{date}</option>
                ))}
              </Form.Select>

              {dateAnalyses && (
                <Tabs>
                  <Tab eventKey="trends" title="Recent Trends">
                    {renderAnalysis(dateAnalyses.recent_trends)}
                  </Tab>
                  <Tab eventKey="clinical" title="Clinical">
                    {renderAnalysis(dateAnalyses.clinical)}
                  </Tab>
                  <Tab eventKey="research" title="Research">
                    {renderAnalysis(dateAnalyses.research)}
                  </Tab>
                </Tabs>
              )}
            </div>
          </Tab>

          <Tab eventKey="system" title="System Status">
            <div style={styles.tabContent}>
              <div className="row">
                <div className="col-md-6">
                  {stats && (
                    <Card className="mb-3">
                      <Card.Body>
                        <h4>System Statistics</h4>
                        <p>Total Analyses: {stats.total_analyses}</p>
                        <p>Unique Dates: {stats.unique_dates}</p>
                        <p>Latest Date: {stats.latest_date}</p>
                        <p>Status: {stats.status}</p>
                        <h5>Analysis Types:</h5>
                        <ul>
                          {Object.entries(stats.type_counts).map(([type, count]) => (
                            <li key={type}>{type}: {count}</li>
                          ))}
                        </ul>
                      </Card.Body>
                    </Card>
                  )}
                </div>
                <div className="col-md-6">
                  {schedulerStatus && (
                    <Card>
                      <Card.Body>
                        <div className="d-flex justify-content-between align-items-center mb-3">
                          <h4 className="mb-0">Scheduler Status</h4>
                          <Button
                            variant="outline-primary"
                            size="sm"
                            onClick={() => fetchWithLoadingState(fetchSchedulerStatus)}
                          >
                            Refresh Status
                          </Button>
                        </div>

                        <p>
                          Status:{' '}
                          <Badge bg={schedulerStatus.status === 'running' ? 'success' : 'warning'}>
                            {schedulerStatus.status}
                          </Badge>
                        </p>

                        <h5>Scheduled Jobs:</h5>
                        <ListGroup>
                          {schedulerStatus.jobs.map(job => (
                            <ListGroup.Item key={job.id}>
                              <div className="d-flex justify-content-between align-items-center">
                                <div>
                                  <strong>{job.name}</strong>
                                  <div className="text-muted small">ID: {job.id}</div>
                                  <div>Next Run: {job.next_run ? new Date(job.next_run).toLocaleString() : 'Not scheduled'}</div>
                                </div>
                                <Badge bg={job.pending ? 'warning' : 'success'}>
                                  {job.pending ? 'Pending' : 'Ready'}
                                </Badge>
                              </div>
                            </ListGroup.Item>
                          ))}
                        </ListGroup>
                      </Card.Body>
                    </Card>
                  )}
                </div>
              </div>

              <Button
                variant="primary"
                onClick={() => fetchWithLoadingState(triggerManualUpdate)}
                className="mt-4"
                disabled={loading}
                style={styles.submitButton}
              >
                {loading ? (
                  <>
                    <Spinner size="sm" className="me-2" />
                    Updating...
                  </>
                ) : (
                  'Trigger Manual Update'
                )}
              </Button>
            </div>
          </Tab>
        </Tabs>
      </Container>
    </div>
  );
}

export default App;