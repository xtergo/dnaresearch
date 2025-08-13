import React from 'react';
import { render, screen } from '@testing-library/react';
import ConsentManagement from './ConsentManagement';

// Mock the API service
jest.mock('../services/api', () => ({
  get: jest.fn(() => Promise.resolve({ data: { forms: [], consents: [] } })),
  post: jest.fn(() => Promise.resolve({ data: {} }))
}));

describe('ConsentManagement', () => {
  test('renders consent management component', () => {
    render(<ConsentManagement userId="test_user" />);
    expect(screen.getByText('🔒 Consent Management')).toBeInTheDocument();
  });

  test('displays loading state initially', () => {
    render(<ConsentManagement userId="test_user" />);
    expect(screen.getByText('Loading consent data...')).toBeInTheDocument();
  });
});