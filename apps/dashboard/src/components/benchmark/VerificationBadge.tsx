/**
 * Verification Badge Component
 * Displays verification status with appropriate icon and styling
 */

import { CheckCircle, Clock, XCircle } from 'lucide-react';
import type { VerificationStatus } from '@/types/benchmark';

interface VerificationBadgeProps {
  status: VerificationStatus;
  size?: 'sm' | 'md';
}

export function VerificationBadge({ status, size = 'md' }: VerificationBadgeProps) {
  const iconSize = size === 'sm' ? 14 : 16;

  const config = {
    verified: {
      icon: <CheckCircle size={iconSize} />,
      label: 'Verified',
      className: 'text-green-700 bg-green-50 border-green-200',
    },
    pending: {
      icon: <Clock size={iconSize} />,
      label: 'Pending',
      className: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    },
    unverified: {
      icon: <XCircle size={iconSize} />,
      label: 'Unverified',
      className: 'text-gray-700 bg-gray-50 border-gray-200',
    },
  };

  const { icon, label, className } = config[status];
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${className} ${sizeClasses}`}
    >
      {icon}
      <span>{label}</span>
    </span>
  );
}
