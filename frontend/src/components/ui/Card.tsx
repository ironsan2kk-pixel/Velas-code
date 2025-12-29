import React from 'react';
import { cn } from '@/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
  noPadding?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverable = false, noPadding = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'card',
          hoverable && 'card-hover cursor-pointer',
          noPadding && 'p-0',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card Header
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  action,
  className,
  ...props
}) => {
  return (
    <div
      className={cn('flex items-center justify-between mb-4', className)}
      {...props}
    >
      <div>
        <h3 className="text-lg font-semibold text-dark-text-primary dark:text-dark-text-primary">
          {title}
        </h3>
        {subtitle && (
          <p className="text-sm text-dark-text-secondary dark:text-dark-text-secondary mt-0.5">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};

CardHeader.displayName = 'CardHeader';

// Card Content
export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardContent: React.FC<CardContentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div className={cn(className)} {...props}>
      {children}
    </div>
  );
};

CardContent.displayName = 'CardContent';

// Card Footer
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardFooter: React.FC<CardFooterProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'mt-4 pt-4 border-t border-dark-border dark:border-dark-border',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

CardFooter.displayName = 'CardFooter';

export default Card;
