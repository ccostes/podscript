import React from 'react';
import Card from './Card';

function SearchList({ podcasts, handleSelect }) {
    const results = podcasts?.map(podcast => <Card key={podcast.collectionId} podcast={podcast} handleSelect={handleSelect} />);
    return (
        <div className='overflow-auto w-[inherit]' style={{height: 50+'vh'}}>
            <ul class="bg-white border border-gray-100 border-b-2 border-gray-100 w-auto bg-white/80 searchList">
                {results}
            </ul>
        </div>
    );
}

export default SearchList;