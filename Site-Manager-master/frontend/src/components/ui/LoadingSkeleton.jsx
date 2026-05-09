/**
 * Reusable Loading Skeleton component
 * @param {Object} props
 * @param {string} props.type - 'card' | 'table' | 'list' | 'page'
 * @param {number} props.count - Number of skeleton items to show
 */
export const LoadingSkeleton = ({ type = 'card', count = 3 }) => {
  const CardSkeleton = () => (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="h-16 flex items-center px-6 gap-4">
        <div className="h-4 w-8 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
      </div>
    </div>
  );

  const TableSkeleton = () => (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="h-12 bg-gray-50 border-b border-gray-100" />
      {[...Array(count)].map((_, i) => (
        <div key={i} className="h-16 border-b border-gray-50 flex items-center px-6 gap-4">
          <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
        </div>
      ))}
    </div>
  );

  const ListSkeleton = () => (
    <div className="space-y-3">
      {[...Array(count)].map((_, i) => (
        <div key={i} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 bg-gray-200 rounded-lg animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-3 w-24 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const PageSkeleton = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="h-8 w-48 bg-gray-200 rounded-lg animate-pulse" />
        <div className="h-10 w-32 bg-gray-200 rounded-xl animate-pulse" />
      </div>
      <CardSkeleton />
      <CardSkeleton />
      <CardSkeleton />
    </div>
  );

  const skeletons = {
    card: () => (
      <div className="space-y-3">
        {[...Array(count)].map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    ),
    table: TableSkeleton,
    list: ListSkeleton,
    page: PageSkeleton,
  };

  const SkeletonComponent = skeletons[type];
  return <SkeletonComponent />;
};

export default LoadingSkeleton;
