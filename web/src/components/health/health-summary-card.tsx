import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface HealthSummaryCardProps {
  title: string;
  value: string | number;
  unit?: string;
  description?: string;
}

export function HealthSummaryCard({
  title,
  value,
  unit,
  description,
}: HealthSummaryCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value}
          {unit && (
            <span className="ml-1 text-sm font-normal text-muted-foreground">
              {unit}
            </span>
          )}
        </div>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
