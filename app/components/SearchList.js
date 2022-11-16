import React from 'react';
import Card from './Card';

function SearchList({ podcasts, handleSelect }) {
    const results = podcasts?.map(podcast => <Card key={podcast.collectionId} podcast={podcast} handleSelect={handleSelect} />);
    return (
        <div className='overflow-auto h-1/2 absolute w-[inherit]'>
            <ul class="bg-white border border-gray-100 w-auto">
                {results}
            </ul>
        </div>
    );
}

export default SearchList;