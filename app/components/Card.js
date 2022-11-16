import React from 'react';

function Card({podcast, handleSelect}) {
    return(
        <li 
            class="flex pl-2 pr-2 py-1 border-b-2 border-gray-100 relative cursor-pointer hover:bg-yellow-50 hover:text-gray-900"
            onClick={event => handleSelect(podcast)}
            >
            <img className='pr-2' src={podcast.artworkUrl60} />
            <div className=''>
                <p className='font-semibold'>{podcast.trackName}</p>
                {podcast.artistName}
            </div>
        </li>
    );
}

export default Card;