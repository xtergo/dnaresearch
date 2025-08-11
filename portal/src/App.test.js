import { render, screen } from '@testing-library/react';
import App from './App';

test('renders theory creation form', () => {
  render(<App />);
  const linkElement = screen.getByText(/DNA Research Platform/i);
  expect(linkElement).toBeInTheDocument();
});

test('renders form fields', () => {
  render(<App />);
  expect(screen.getByLabelText(/Theory ID/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Version/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Scope/i)).toBeInTheDocument();
});